from datetime import datetime

from bson import ObjectId
from pydash import get

from connect import redis_cluster, web3_providers
from enums.user import SignInProviders
from helper.account.account import AccountsHelpers
from helper.name_services import NameServicesHelpers
from helper.template.category import TemplateCategoriesHelpers
from helper.template.template import TemplateHelpers
from lib import NotFound, BadRequest, Forbidden, get_name_services
from lib.utils import is_oid, dt_utcnow
from models import UsersModel, UsersTemplatesModel, UsersPurchaseHistoriesModel, NFTContractsModel, AccountsModel
from services.authentication.auth import AuthServices
from services.social.google import GoogleServices
from tasks import task_save_user, task_save_ens_name
from tasks.user_template import task_user_purchase_template


class UsersServices:

    @classmethod
    def get_info_by_address(cls, address: str):
        _user = UsersModel.find_one(filter={
            'public_address': address.lower()
        })

        if _user is None:
            raise NotFound(msg="Can't find user match with this address.")

        return {
            'username': get(_user, 'username', 'Unnamed'),
            'avatar': get(_user, 'avatar', ''),
            'public_address': get(_user, 'public_address'),
            'created_time': get(_user, 'created_time'),
        }

    @classmethod
    def get_info_by_email(cls, email: str):
        _user = AccountsHelpers.user_of(email=email)

        if not _user:
            raise NotFound(msg="Can't find user match with this email.")

        return {
            'username': get(_user, 'username', 'Unnamed'),
            'avatar': get(_user, 'avatar', ''),
            'public_address': get(_user, 'public_address'),
            'created_time': get(_user, 'created_time'),
        }

    @classmethod
    def update_info(
            cls,
            login_info: dict,
            username: str,
            avatar: str,
            google_token: str,
            public_address: str,
            signature: str,
            chain: int,
            nonce: str
    ):
        _user_id = get(login_info, 'user._id')
        _email = ''
        _wallet_address = ''

        _user_data = {}
        if username:
            _user_data['username'] = username
        if avatar:
            _user_data['avatar'] = avatar
        task_save_user.delay(
            user=str(_user_id),
            user_data={
                'username': username,
                'avatar': avatar
            }
        )

        if google_token:
            """
               - Verify google token
            """
            _info = GoogleServices.verify(google_token)

            if not _info:
                raise BadRequest(msg='Invalid params.', errors=['Google token invalid.'])

            _email = get(_info, 'email')

            AccountsModel.insert_one({
                'email': _email,
                'provider': SignInProviders.GOOGLE,
                'user': ObjectId(_user_id),
                'active': True,
                'info': _info.__dict__.get('_data'),
                'created_time': dt_utcnow(),
                'updated_time': dt_utcnow(),
                'created_by': 'inz-api:services:user:update_info',
                'updated_by': ''
            })

        if public_address and signature and chain and nonce:
            """
                - Verify signature
            """

            _web3 = get(web3_providers, str(chain))
            _msg, _nonce = AuthServices.get_validate_msg(nonce=nonce)

            _real_public_address = _web3.recover_address_from_msg_sign(msg=_msg, signature=signature)

            if _real_public_address.lower() != public_address.lower():
                raise BadRequest(msg='Invalid params.', errors=['Invalid wallet signature.'])

            _wallet_address = public_address.lower()

            task_save_user.delay(
                user=str(_user_id),
                wallet={
                    'public_address': public_address
                }
            )

        return {
            'username': username,
            'avatar': avatar,
            'email': _email,
            'public_address': _wallet_address
        }

    @classmethod
    def update_ens_name(cls, login_info: dict, ens_name: str):
        _user_id = get(login_info, 'user._id')
        _address = get(login_info, 'public_address')

        _result = get_name_services(redis_cluster=redis_cluster, address=_address)

        if not _result:
            raise BadRequest(msg="Invalid params.", errors=["You aren't owner of this ens name."])

        _is_found = False
        for item in _result:
            if ens_name in get(item, 'list_domain', []):
                _is_found = True

        if not _is_found:
            raise BadRequest(msg="Invalid params.", errors=["You aren't owner of this ens name."])

        task_save_ens_name.delay(
            user=str(_user_id),
            ens_name=ens_name,
        )

        return {
            'ens_name': ens_name,
        }

    @classmethod
    def get_templates(
            cls,
            user: str = None,
            page: int = 1,
            page_size: int = 10,
            category: str = None,
            template: str = None,
    ):
        _filter = {'user_id': ObjectId(user)}

        if category is not None:
            if not is_oid(category) or not TemplateCategoriesHelpers.is_exist(category_id=category):
                raise BadRequest(msg="Invalid params.", errors=["This category doesn't exist."])
            _filter['category_id'] = ObjectId(category)

        if template is not None:
            if not is_oid(template) or not TemplateHelpers.is_exist(template_id=template):
                raise BadRequest(msg="Invalid params.", errors=["This template doesn't exist."])
            _filter['template_id'] = ObjectId(template)

        _offset = page > 0 and (page - 1) * page_size or 0

        _pipeline = [
            {
                '$match': _filter
            },
            {
                '$lookup': {
                    'from': 'template_categories',
                    'localField': 'category_id',
                    'foreignField': '_id',
                    'as': 'category',
                }
            },
            {
                '$unwind': '$category'
            },
            {
                '$lookup': {
                    'from': 'templates',
                    'localField': 'template_id',
                    'foreignField': '_id',
                    'as': 'template',
                }
            },
            {
                '$unwind': '$template'
            },
            {
                '$skip': _offset
            },
            {
                '$limit': page_size
            },
            {
                '$project': {
                    '_id': 1,
                    'template_id': 1,
                    'template': {
                        'title': '$template.title',
                        'description': '$template.description',
                        'thumbnail': '$template.thumbnail',
                        'price': '$template.price',
                        'author': '$template.author'
                    },
                    'category_id': 1,
                    'category_name': '$category.name',
                    'created_time': 1
                }
            }
        ]

        _items = UsersTemplatesModel.col.aggregate(pipeline=_pipeline)

        _items = list(_items)

        _num_of_page = (len(_items) / page_size)
        if (len(_items) % page_size) > 0:
            _num_of_page = _num_of_page + 1

        return {
            'items': _items,
            'page': page,
            'page_size': page_size,
            'num_of_page': _num_of_page
        }

    @classmethod
    def get_purchase_histories(
            cls,
            user: str = None,
            page: int = 1,
            page_size: int = 10,
            category: str = None,
            sort: str = None,
            start_time: float = None,
            end_time: float = None
    ):
        _filter = {'user_id': ObjectId(user)}

        if category is not None:
            if not is_oid(category) or not TemplateCategoriesHelpers.is_exist(category):
                raise BadRequest(msg="Invalid params.", errors=["This category doesn't exist."])
            _filter['category_id'] = ObjectId(category)

        if start_time:
            _filter['created_time'] = {
                '$gte': datetime.utcfromtimestamp(start_time)
            }
            if end_time:
                _filter['created_time']['$lte'] = datetime.utcfromtimestamp(end_time)

        _offset = page > 0 and (page - 1) * page_size or 0

        _pipeline = [
            {
                '$match': _filter
            },
            {
                '$lookup': {
                    'from': 'template_categories',
                    'localField': 'category_id',
                    'foreignField': '_id',
                    'as': 'category',
                }
            },
            {
                '$unwind': '$category'
            },
            {
                '$lookup': {
                    'from': 'templates',
                    'localField': 'template_id',
                    'foreignField': '_id',
                    'as': 'template',
                }
            },
            {
                '$unwind': '$template'
            },
            {
                '$skip': _offset
            },
            {
                '$limit': page_size
            },
            {
                "$sort": {
                    "created_time": sort
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'template_id': 1,
                    'template': {
                        'title': '$template.title',
                        'description': '$template.description',
                        'thumbnail': '$template.thumbnail',
                        'price': '$template.price',
                    },
                    'category_id': 1,
                    'category_name': '$category.name',
                    'original_price': 1,
                    'purchase_price': 1,
                    'discount': 1,
                    'payment': 1,
                    'created_time': 1
                }
            }
        ]

        _items = UsersPurchaseHistoriesModel.col.aggregate(pipeline=_pipeline)

        _items = list(_items)

        _num_of_page = (len(_items) / page_size)
        if (len(_items) % page_size) > 0:
            _num_of_page = _num_of_page + 1

        return {
            'items': _items,
            'page': page,
            'page_size': page_size,
            'num_of_page': _num_of_page
        }

    @classmethod
    def purchase_template(cls, user, template):
        _template = TemplateHelpers.get_by_id(template_id=template)

        if _template is None:
            raise BadRequest(msg='Invalid params.', errors=['Template does not exist.'])

        # TODO: payment
        _user_template = UsersTemplatesModel.insert_one({
            'user_id': ObjectId(user),
            'template_id': get(_template, '_id'),
            'category_id': ObjectId(get(_template, 'category_id')),
            'contracts': [],
            'website_domain': [],
            'created_by': 'inz-dapp-api:tasks:task_user_purchase_template',
            'updated_by': ''
        })

        UsersPurchaseHistoriesModel.insert_one({
            'user_id': ObjectId(user),
            'template_id': get(_template, '_id'),
            'category_id': ObjectId(get(_template, 'category_id')),
            'original_price': 0,
            'purchase_price': 0,
            'discount': {},
            'payment': {},
            'created_by': 'inz-dapp-api:services:UserServices:purchase_template',
            'updated_by': ''
        })

        task_user_purchase_template.delay(user_id=user, user_template_id=str(get(_user_template, '_id')),
                                          template_id=template)

        return _user_template

    @classmethod
    def get_contracts(
            cls,
            user: str = None,
            page: int = 1,
            page_size: int = 10
    ):
        _filter = {'user_id': ObjectId(user)}

        _results = UsersTemplatesModel.find(filter=_filter)

        if not _results:
            return {
                'items': [],
                'page': 1,
                'page_size': 10,
                'num_of_page': 0
            }

        _contracts = []
        _contracts_mapping = []
        for result in _results:
            _user_template_id = get(result, '_id')
            _subdomains = get(result, 'website_domain', [])
            _full_domains = get(result, 'full_domain', [])
            for index, item in enumerate(get(result, 'contracts', [])):
                if str(item) not in _contracts:
                    _contracts.append(str(item))
                    _contracts_mapping.append({
                        'user_template_id': _user_template_id,
                        'contract_id': item,
                        'subdomain': get(_subdomains, f'[{index}]', ''),
                        'full_domain': get(_full_domains, f'[{index}]', ''),
                    })

        _user_contracts = []
        for item in _contracts_mapping:
            _contract_id = str(get(item, 'contract_id'))
            _nft_contract = NFTContractsModel.find_one(filter={'_id': ObjectId(_contract_id)})
            _create_smc_status_key = f'smc:_id:{_contract_id}:create_smc:status'
            _create_smc_status = redis_cluster.get(_create_smc_status_key)
            _user_contracts.append({
                'user_template_id': get(item, 'user_template_id'),
                'release_status': _create_smc_status,
                'subdomain': get(item, 'subdomain'),
                'full_domain': get(item, 'full_domain'),
                **_nft_contract,
            })

        _sort_function = lambda item: get(item, '_id')
        _user_contracts.sort(key=_sort_function, reverse=True)

        _offset = page > 0 and (page - 1) * page_size or 0
        _num_of_page = (len(_user_contracts) / page_size)
        _items = _user_contracts[_offset:page_size + _offset]
        if (len(_user_contracts) % page_size) > 0:
            _num_of_page = _num_of_page + 1

        return {
            'items': _items,
            'page': page,
            'page_size': page_size,
            'num_of_page': _num_of_page
        }

    @classmethod
    def get_contract_by_id(
            cls,
            user: str,
            contract_id: str
    ):
        _filter = {'user_id': ObjectId(user)}
        _pipeline = [
            {
                '$match': _filter
            },
            {
                '$lookup': {
                    'from': 'templates',
                    'localField': 'template_id',
                    'foreignField': '_id',
                    'as': 'template',
                }
            },
            {
                '$unwind': '$template'
            },
            {
                '$lookup': {
                    'from': 'nft_contracts',
                    'localField': 'contracts',
                    'foreignField': '_id',
                    'as': 'collections',
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'template_id': 1,
                    'template': {
                        'title': '$template.title',
                        'description': '$template.description',
                        'thumbnail': '$template.thumbnail',
                    },
                    'collection': {
                        '$filter': {
                            'input': '$collections',
                            'as': 'collection',
                            'cond': {
                                '$eq': ['$$collection._id', ObjectId(contract_id)]
                            }
                        }
                    }
                }
            },
            {'$unwind': '$collection'}
        ]

        _items = UsersTemplatesModel.col.aggregate(pipeline=_pipeline)

        _items = list(_items)

        if not get(_items, '[0].collection', {}):
            raise BadRequest(msg="Collection isn't exist or not owned.")

        _user_template_id = get(_items[0], '_id')
        _user_template = UsersTemplatesModel.find_one(filter={'_id': ObjectId(_user_template_id)})
        _subdomains = get(_user_template, 'website_domain', [])
        _full_domains = get(_user_template, 'full_domain', [])

        _subdomain = get(_subdomains, '[0]', '')
        _full_domain = get(_full_domains, '[0]', '')

        _create_domain_status_key = f'smc:user_template_id:{_user_template_id}:create_domain:{_subdomain}:status'
        _create_domain_status = redis_cluster.get(_create_domain_status_key)

        _create_smc_status_key = f'smc:_id:{contract_id}:create_smc:status'
        _create_smc_status = redis_cluster.get(_create_smc_status_key)

        return {
            **_items[0],
            'subdomain': _subdomain,
            'full_domain': _full_domain,
            'create_domain_status': _create_domain_status,
            'create_contract_status': _create_smc_status,
        }

    @classmethod
    def get_profile(cls, user: str):
        _user = UsersModel.find_one(filter={'_id': ObjectId(user)})

        if not _user:
            raise Forbidden(
                msg='Please login to continue.',
                errors=[{
                    'token': 'Invalid.'
                }]
            )

        # _pipeline = [
        #     {
        #         '$match': {
        #             '_id': ObjectId(user),
        #         }
        #     },
        #     {
        #         '$lookup': {
        #             'from': 'accounts',
        #             'localField': '_id',
        #             'foreignField': 'user',
        #             'as': 'provider',
        #         }
        #     },
        #     {
        #         '$unwind': '$provider'
        #     },
        #     {
        #         '$project': {
        #             '_id': 1,
        #             'username': 1,
        #             'provider': {
        #                 'email': '$provider.email',
        #                 'provider': '$provider.provider',
        #                 'last_login': {
        #                     '$toLong': '$provider.info.lastLoginAt'
        #                 },
        #             },
        #             'avatar': 1,
        #             'public_address': 1,
        #             'last_login': 1
        #         }
        #     }
        # ]

        if get(_user, 'username', 'Unnamed') == 'Unnamed':
            _domain_list = NameServicesHelpers.get_base_name_services(address=get(_user, 'public_address'))
            if _domain_list:
                _user['username'] = get(_domain_list, '[0]', 'Unnamed')

        # _user = UsersModel.find_one({'_id': ObjectId(user)})
        _provider = AccountsModel.find_one({'user': ObjectId(user)})
        _wallet_last_login = get(_user, 'last_login')

        if isinstance(_wallet_last_login, datetime):
            if int(int(get(_provider, 'info.lastLoginAt', 0)) / 1000) > int(_wallet_last_login.timestamp()):
                _user['last_login'] = datetime.utcfromtimestamp(int(get(_provider, 'info.lastLoginAt', 0)) / 1000)

        return {
            **_user,
            'provider': {
                'email': get(_provider, 'email', ''),
                'provider': get(_provider, 'provider', ''),
                'last_login': int(get(_provider, 'info.lastLoginAt', 0))
            }
        }
