import pydash as py_
import bson
from enums.template import TemplateBlockType
from exceptions.block_type import BlockTypeNotSameEx
from exceptions.requests import IsNotValidObjIdEx
from exceptions.template_content import DomainNotFoundEx, TemplateContentNotFoundEx, UserNotOwnTemplateEx

from helper.template.block_type import BlockTypeHelper
from lib.enum import ContractInsertType
from models import NFTContractsModel, TemplateContentModel, TemplatesModel, UsersTemplatesModel
from schemas import NftContractContentSchema, NftSchema
from schemas.template.block_type import ALL_RAW_BLOCK_TYPE_SCHEMA
from schemas.template.template_content import TemplateContentSchema

class TemplateContentService:

    # Utils
    @staticmethod
    def dump_template_blocks(template_contents):
        _return_data = []
        for _block in template_contents:
            _block_type = py_.get(_block, 'block_type')
            if not _block_type in ALL_RAW_BLOCK_TYPE_SCHEMA:
                _return_data.append(_block)

            #NOTE: load data of block first
            _block_data = ALL_RAW_BLOCK_TYPE_SCHEMA[_block_type].load(py_.get(_block, 'data'))

            #NOTE: load content all of block
            _block = TemplateContentSchema().load(_block)
            _return_data.append({
                '_id': py_.get(_block, '_id'),
                'block_type': _block_type,
                'data': _block_data,
                'user_template_id': py_.get(_block, 'user_template_id')
            })

        return _return_data

    @staticmethod
    def get_mint_block_data(block):
        _block_data = py_.get(block, 'data')
        if not _block_data:
            return block

        _nft_contracts = py_.get(_block_data, 'items')
        _mint_contracts = []
        _list_nft_contracts = {}
        for _item in _nft_contracts:
            _nft_contract_id = py_.get(_item, 'nft_contract_id')

            _nft_contract = None
            if not _nft_contract_id in _list_nft_contracts:
                _nft_contract = NFTContractsModel.find_one({
                    '_id': bson.objectid.ObjectId(_nft_contract_id)
                })
                if not _nft_contract:
                    continue

                _list_nft_contracts[_nft_contract_id] = _nft_contract

            _nft_contract = _list_nft_contracts[_nft_contract_id]

            _nft_index_type = py_.get(_item, 'index_type')
            _mint_item = {
                'chain_id': py_.get(_nft_contract, 'chain_id'),
                'contract': py_.get(_nft_contract, 'contract'),
                'chain': py_.get(_nft_contract, 'chain'),
                'highlight_text': py_.get(_nft_contract, 'highlight_text'),
                'currency': py_.get(_nft_contract, 'currency'),
                'deploy_address': py_.get(_nft_contract, 'deploy_address'),
                'currency_address': py_.get(_nft_contract, 'currency_address'),
                'symbol': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.symbol'),
                'image_url': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.image_url'),
                'name': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.name'),
                'price': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.price'),
                'properties': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.properties'),
                'supply': py_.get(_nft_contract, f'nft_list.{_nft_index_type - 1}.supply'),
                'dapp_creator_address': py_.get(_nft_contract, 'dapp_creator_address'),
                'gateway_nft_address': py_.get(_nft_contract, 'gateway_nft_address'),
                'factory_address': py_.get(_nft_contract, 'factory_address'),
                'index_type': _nft_index_type,
            }
            _mint_contracts.append(_mint_item)

        _items = NftContractContentSchema(many=True).dump(_mint_contracts)
        py_.set_(block, 'data.items', _items)

        return block

    @staticmethod
    def get_marketplace_block_data(block, template_detail):
        _contract_address = py_.get(template_detail, 'contract_address', [])
        py_.set_(block, 'data.contract_address', _contract_address)
        return block

    @staticmethod
    def create(form_data):
        '''
        '''
        _user_template_id = py_.get(form_data, 'user_template_id')
        _content_data = BlockTypeHelper.validate(data=form_data)
        _insert_data = {
            'data': _content_data,
            'user_template_id': _user_template_id,
            'created_by': 'inz-dapp-api:services:TemplateContentService:create'
        }
        TemplateContentModel.insert_one(_insert_data)
        return _insert_data

    @staticmethod
    def update(user_id, template_content_id, form_data):
        if not bson.objectid.ObjectId.is_valid(template_content_id):
            raise IsNotValidObjIdEx()

        _template_content = TemplateContentModel.find_one({
            '_id': bson.objectid.ObjectId(template_content_id)
        })

        if not _template_content:
            raise TemplateContentNotFoundEx

        if str(py_.get(_template_content, 'user_id')) != user_id:
            raise UserNotOwnTemplateEx

        _content_data = BlockTypeHelper.validate(data={
            **form_data,
            'block_type': py_.get(_template_content, 'block_type')
        }, template_content=_template_content)
        _update_data = {
            'data': _content_data,
            'updated_by': 'inz-dapp-api:services:TemplateContentService:update'
        }
        TemplateContentModel.update_one({
            '_id': bson.objectid.ObjectId(template_content_id),
        }, _update_data)

        return {
            '_id': template_content_id,
            'block_type': py_.get(_template_content, 'block_type')
        }

    @staticmethod
    def get_detail_template_data(template_contents):
        _user_template = UsersTemplatesModel.find_one({
            '_id': bson.objectid.ObjectId(py_.get(template_contents, '0.user_template_id'))
        })

        _contracts = py_.get(_user_template, 'contracts', [])

        _contract_ids = [bson.objectid.ObjectId(x) for x in _contracts]
        # NOTE: get contract of each template content
        _nft_contracts = NFTContractsModel.find({
            '_id': {
                '$in': _contract_ids
            },
            'is_released': True
        })

        _contract_address = [py_.get(x, 'contract') for x in _nft_contracts]

        _template = TemplatesModel.find_one({
            '_id': py_.get(_user_template, 'template_id')
        })
        _demo_url = py_.get(_template, 'demo_url')

        return {
            'contract_ids': _contract_ids,
            'contract_address': _contract_address,
            'demo_url': _demo_url,
            'template_id': py_.get(_template, '_id'),
            'user_template_id': py_.get(_user_template, '_id')
        }

    @staticmethod
    def get_block_detail_for_template_contents(template_detail, template_contents):

        for _block in template_contents:
            _block_type = py_.get(_block, 'block_type')

            py_.set_(_block, '_id', py_.to_string(py_.get(_block, '_id')))
            if _block_type == TemplateBlockType.BLOCK_MINT_NFT:
                _block = TemplateContentService.get_mint_block_data(block=_block)
            if _block_type == TemplateBlockType.BLOCK_MARKETPLACE:
                _block = TemplateContentService.get_marketplace_block_data(block=_block, template_detail=template_detail)

        return template_contents
        

    @staticmethod
    def get_content_by_user_template_id(user_template_id):
        '''
            - This function only return metadata -> not return current live data in db
        '''
        if not bson.objectid.ObjectId.is_valid(user_template_id):
            raise IsNotValidObjIdEx()

        _template_contents = TemplateContentModel.find({
            'user_template_id': bson.objectid.ObjectId(user_template_id)
        })

        if not _template_contents:
            raise TemplateContentNotFoundEx

        _template_contents = TemplateContentService.dump_template_blocks(template_contents=_template_contents.copy())

        _template_detail = TemplateContentService.get_detail_template_data(template_contents=_template_contents)

        _template_contents = TemplateContentService.get_block_detail_for_template_contents(template_detail=_template_detail.copy(), template_contents=_template_contents.copy())

        return {
            **_template_detail,
            'template_contents': _template_contents,
        }

    @staticmethod
    def get_template_content_by_domain(website_domain, params):
        _user_template = UsersTemplatesModel.find_one({
            'full_domain': website_domain
        })

        if not _user_template:
            raise DomainNotFoundEx

        _template_contents = TemplateContentModel.find({
            'user_template_id': py_.get(_user_template, '_id')
        })
        
        if not _template_contents:
            raise TemplateContentNotFoundEx

        _template_contents = TemplateContentService.dump_template_blocks(template_contents=_template_contents.copy())

        _template_detail = TemplateContentService.get_detail_template_data(template_contents=_template_contents)

        _template_contents = TemplateContentService.get_block_detail_for_template_contents(template_detail=_template_detail.copy(), template_contents=_template_contents.copy())

        return {
            **_template_detail,
            'template_contents': _template_contents,
        }

