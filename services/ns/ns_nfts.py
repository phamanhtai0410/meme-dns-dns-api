import datetime
import pydash as py_
from lib.enums.nft import MarketplaceAction
from lib.utils import dt_utcnow
import traceback
import bson

from exceptions.nfts import NftIsNotOnMarketEx, NftIsOnMarketEx, NftNotFoundEx, UserNotOwnNftEx
from exceptions.requests import IsNotValidObjIdEx

from models import NsNftModel, OrdersModel

from eth_account import Account
from eth_utils import from_wei, to_checksum_address
from eth_account.messages import encode_structured_data
from config import Config


class NsNFTsService:
    
    @classmethod
    def get_user_list(cls, params):
        _page = py_.get(params, 'page')
        _page_size = py_.get(params, 'page_size')
        _owner = py_.get(params, 'owner')
        _search = py_.get(params, 'search')

        _result = NsNFTsService.get_nfts(
            page=_page,
            page_size=_page_size,
            filter={
                'owner': _owner.lower()
            },
            search=_search
        )

        return _result

    @staticmethod
    def is_nft_on_market(item):
        _buy_deadline = py_.get(item, 'buy_deadline').timestamp() if py_.get(item, 'buy_deadline') else 0
        _now = dt_utcnow().timestamp()
        _on_market = True if _buy_deadline > _now else False
        return _on_market

    @staticmethod
    def mapping_nft_detail(nft_items):
        _nft_contracts = {}

        def get_nft_detail(item):
            _on_market = NsNFTsService.is_nft_on_market(item=item)
            return {
                **item,
                'chain_id': py_.get(item, 'chain_id'),
                # NOTE: if nft does not have previous price on sale will get default price
                'price': py_.get(item, 'price'),
                'on_market': _on_market,
            }

        _items = []

        for _item in nft_items:
            # NOTE: get detail of nft
            _item = get_nft_detail(_item)
            _items.append(_item)

        return _items


    @classmethod
    def get_nfts(
            cls,
            page=1,
            page_size=10,
            chain: str = None,
            sort_field: str = None,
            sort_type: str = None,
            filter = {},
            search = None,
    ):
        _filter = {
            **filter
        }
        _func_sort = None
        _sort = None

        if search:
            _filter = {
                **_filter,
                'domain_name': {
                    '$regex': search, '$options': 'i'
                }
            }

        if sort_field and sort_type:
            _func_sort = lambda x: py_.get(x, sort_field)
            _sort = 1 if sort_type == 'asc' else -1

        _results = NsNftModel.page(
            filter=_filter,
            page=page,
            page_size=page_size,
            sort=_sort,
            func_sort=_func_sort
        )

        _items = NsNFTsService.mapping_nft_detail(py_.get(_results, 'items'))

        print(_items)

        py_.set_(_results, 'items', _items)


        return _results

    @classmethod
    def get_nft_by_id(
        cls,
        nft_id,
    ):
        if not bson.objectid.ObjectId.is_valid(nft_id):
            raise IsNotValidObjIdEx
        
        _nft = NsNftModel.find_one({
            '_id': bson.objectid.ObjectId(nft_id)
        })

        if not _nft:
            raise NftNotFoundEx

        return py_.get(_nft, '0')

    @staticmethod
    def get_marketplace_nfts(params):
        _page = py_.get(params, 'page', default=1)
        _page_size = py_.get(params, 'page_size', default=10)
        _sort_field = py_.get(params, 'sort_field', default=None)
        _sort_type = py_.get(params, 'sort_type', default=None)

        # NOTE: if buy_deadline existed and valid with time -> on_market will mark at true
        _result = NsNFTsService.get_nfts(
            filter={
                'buy_deadline': {
                    '$gt': dt_utcnow()
                }
            },
            page=_page,
            page_size=_page_size,
            sort_field=_sort_field,
            sort_type=_sort_type,
        )

        return _result

    @staticmethod
    def get_by_token_id(params):
        _token_id = py_.get(params, 'token_id')

        _result = NsNFTsService.get_nfts(
            filter={
                'token_id': _token_id
            }
        )

        _result = py_.get(_result, 'items.0', None)

        print(_result)

        if not _result:
            raise NftNotFoundEx


        return _result

    @classmethod
    def verify_sell_signature(cls, data):
        '''
        '''
        try:
            _signature_schema = {
                "domain": {
                    "chainId": None,
                    "name": "Sell Domain",
                    "verifyingContract": "",
                    "version": "1"
                },
                "message": {
                    "domain_name": "",
                    "token_id": "",
                    "nft_id": "",
                    "buy_deadline": None,
                    "price": None
                },
                "primaryType": "Domain",
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "Domain": [
                        {"name": "domain_name", "type": "string"},
                        {"name": "token_id", "type": "string"},
                        {"name": "nft_id", "type": "string"},
                        {"name": "buy_deadline", "type": "uint256"},
                        {"name": "price", "type": "uint256"}
                    ]
                }
            }
            _chain_id =  py_.get(data, 'chain_id')
            _domain_name = py_.get(data, 'domain_name')
            _token_id = py_.get(data, 'token_id')
            _nft_id = py_.get(data, 'nft_id')
            _buy_deadline = py_.get(data, 'buy_deadline')
            _price = py_.get(data, 'price')

            py_.set_(_signature_schema, 'domain.chainId', _chain_id)
            py_.set_(_signature_schema, 'domain.verifyingContract', to_checksum_address(Config.MARKETPLACE_CONTRACT))
            py_.set_(_signature_schema, 'message.domain_name', _domain_name)
            py_.set_(_signature_schema, 'message.token_id', _token_id)
            py_.set_(_signature_schema, 'message.nft_id', _nft_id)
            py_.set_(_signature_schema, 'message.buy_deadline', _buy_deadline)
            py_.set_(_signature_schema, 'message.price', _price)

            _structured_msg = encode_structured_data(_signature_schema)
            _signature = py_.get(data, 'signature')
            _recovered_address = Account.recover_message(_structured_msg, signature=_signature)

            return _recovered_address
        except:
            traceback.print_exc()
            return ''

    @classmethod
    def verify_cancel_sell_signature(cls, data):
        '''
        '''
        try:
            _signature_schema = {
                "domain": {
                    "chainId": None,
                    "name": "Cancel Sell Domain",
                    "verifyingContract": "",
                    "version": "1"
                },
                "message": {
                    "domain_name": "",
                    "token_id": "",
                    "nft_id": "",
                },
                "primaryType": "Domain",
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "Domain": [
                        {"name": "domain_name", "type": "string"},
                        {"name": "token_id", "type": "string"},
                        {"name": "nft_id", "type": "string"}
                    ]
                }
            }
            _chain_id =  py_.get(data, 'chain_id')
            _domain_name = py_.get(data, 'domain_name')
            _token_id = py_.get(data, 'token_id')
            _nft_id = py_.get(data, 'nft_id')

            py_.set_(_signature_schema, 'domain.chainId', _chain_id)
            py_.set_(_signature_schema, 'domain.verifyingContract', to_checksum_address(Config.MARKETPLACE_CONTRACT))
            py_.set_(_signature_schema, 'message.domain_name', _domain_name)
            py_.set_(_signature_schema, 'message.token_id', _token_id)
            py_.set_(_signature_schema, 'message.nft_id', _nft_id)

            _structured_msg = encode_structured_data(_signature_schema)
            _signature = py_.get(data, 'signature')
            _recovered_address = Account.recover_message(_structured_msg, signature=_signature)

            return _recovered_address
        except:
            traceback.print_exc()
            return ''

    @staticmethod
    def sell_nfts_by_signature(form_data):
        _nft_id = py_.get(form_data, 'nft_id')
        _price = py_.get(form_data, 'price')

        if not bson.objectid.ObjectId.is_valid(_nft_id): 
            raise IsNotValidObjIdEx

        _nft = NsNftModel.find_one({
            '_id': bson.objectid.ObjectId(_nft_id)
        })

        if NsNFTsService.is_nft_on_market(item=_nft):
            raise NftIsOnMarketEx

        _signature_address = NsNFTsService.verify_sell_signature(data={
            **form_data,
            'domain_name': py_.get(_nft, 'domain_name'),
            'chain_id': py_.to_integer(py_.get(_nft, 'chain_id')),
            'token_id': py_.get(_nft, 'token_id'),
            'price': _price
        })

        if _signature_address.lower() != py_.get(_nft, 'owner'): 
            raise UserNotOwnNftEx

        _buy_deadline = py_.get(form_data, 'buy_deadline')

        _deadline = dt_utcnow() + datetime.timedelta(days=_buy_deadline)

        _order_id = NsNftModel.sell_nft(sell_data={
            **form_data,
            'price': '{0:f}'.format((from_wei(_price, 'ether'))),
            'buy_deadline': _deadline
        })

        _log_data = {
            **_nft,
            **form_data,
            'buy_deadline': _deadline
        }

        OrdersModel.insert_one({
            'chain': py_.get(_log_data, 'chain'),
            'token_id': py_.get(_log_data, 'token_id'),
            'order_id': _order_id,
            'price': py_.get(_log_data, 'price'),
            'nft_id': py_.get(_log_data, 'nft_id'),
            'sender': py_.get(_log_data, 'user_address'),
            'receiver': None,
            'action': MarketplaceAction.SELL,
            'data': _log_data,
            'created_by': 'dns-api:services:NFTsServices:sell_user_nfts'
        })

        return {}
        
    @staticmethod
    def cancel_sell_nfts_by_signature(form_data):

        _nft_id = py_.get(form_data, 'nft_id')

        if not bson.objectid.ObjectId.is_valid(_nft_id): 
            raise IsNotValidObjIdEx

        _price = py_.get(form_data, 'price')

        _nft = NsNftModel.find_one({
            '_id': bson.objectid.ObjectId(_nft_id)
        })

        if not NsNFTsService.is_nft_on_market(item=_nft):
            raise NftIsNotOnMarketEx

        _signature_address = NsNFTsService.verify_cancel_sell_signature(data={
            **form_data,
            'domain_name': py_.get(_nft, 'domain_name'),
            'chain_id': py_.to_integer(py_.get(_nft, 'chain_id')),
            'token_id': py_.get(_nft, 'token_id'),
        })

        if _signature_address.lower() != py_.get(_nft, 'owner'): 
            raise UserNotOwnNftEx

        NsNftModel.cancel_sell_nft(nft_id=_nft_id)

        OrdersModel.insert_one({
            'chain': py_.get(_nft, 'chain'),
            'token_id': py_.get(_nft, 'token_id'),
            'order_id': py_.get(_nft, 'order_id'),
            'price': py_.get(_nft, 'price'),
            'sender': py_.get(_nft, 'owner'),
            'receiver': None,
            'nft_id': bson.objectid.ObjectId(_nft_id),
            'action': MarketplaceAction.CANCEL_SELL,
            'data': _nft,
            'created_by': 'dns-api:services:NFTsServices:sell_user_nfts'
        })


        return {}

    @classmethod
    def get_nft_by_domain(cls, domain_name):
        _result = NsNftModel.find_one({
            'domain_name': domain_name
        })

        if not _result:
            raise NftNotFoundEx

        return _result