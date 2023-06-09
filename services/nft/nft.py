import datetime
import traceback

import web3
import pydash as py_
import bson
from bson import ObjectId

from exceptions.nfts import NftIsOnMarketEx, NftNotFoundEx, UserNotOwnNftEx
from exceptions.requests import IsNotValidObjIdEx
from lib.enums.nft import MarketplaceAction
from lib.logger import debug
from models import OrdersModel, DevMintOrdersModel, NsNftModel
from lib import dt_utcnow
from connect import redis_cluster
from worker import worker

class NFTsServices:

    @staticmethod
    def is_nft_on_market(item):
        _buy_deadline = py_.get(item, 'buy_deadline').timestamp() if py_.get(item, 'buy_deadline') else 0
        _now = dt_utcnow().timestamp()
        _on_market = True if _buy_deadline > _now else False
        return _on_market

    @staticmethod
    def mapping_nft_detail(nft_items):
        _nft_contracts = {}

        def get_nft_detail(item, contract):
            _on_market = NFTsServices.is_nft_on_market(item=item)
            return {
                **item,
                'chain_id': py_.get(_nft_contracts[contract], 'chain_id'),
                'chain': py_.get(_nft_contracts[contract], 'chain'),
                # NOTE: if nft does not have previous price on sale will get default price
                'price': py_.get(item, 'price'),
                'on_market': _on_market,
            }

        _items = []

        for _item in nft_items:
            _contract = py_.get(_item, 'contract').lower()
            # NOTE: get detail of nft
            _item = get_nft_detail(_item, _contract)
            _items.append(_item)

        return _items

    @classmethod
    def get_nfts(
            cls,
            page,
            page_size: int,
            chain: str = None,
            contracts: str = None,
            sort_field: str = None,
            sort_type: str = None,
            user_id: str = None,
            filter={}
    ):
        _filter = {
            **filter
        }
        _func_sort = None
        _sort = None

        if chain is not None:
            _filter['chain'] = chain

        if contracts:
            _web3 = web3.Web3()
            _contracts = [x.lower() for x in contracts if _web3.isAddress(x)]
            if not _contracts:
                return {}

            if _contracts:
                _filter['contract'] = {
                    '$in': _contracts
                }

        if user_id and bson.objectid.ObjectId.is_valid(user_id):
            _filter['user'] = bson.objectid.ObjectId(user_id)

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

        _items = NFTsServices.mapping_nft_detail(py_.get(_results, 'items'))

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

        # mapping nft detail will map and return list
        _nft = NFTsServices.mapping_nft_detail([_nft])

        return py_.get(_nft, '0')

    @staticmethod
    def get_marketplace_by_contracts(params):
        _page = py_.get(params, 'page', default=1)
        _page_size = py_.get(params, 'page_size', default=10)
        _chain = py_.get(params, 'chain', default=None)
        _sort_field = py_.get(params, 'sort_field', default=None)
        _sort_type = py_.get(params, 'sort_type', default=None)
        _contracts = py_.get(params, 'contracts', default=None)

        if not _contracts:
            return {}

        # NOTE: if buy_deadline existed and valid with time -> on_market will mark at true
        _result = NFTsServices.get_nfts(
            filter={
                'buy_deadline': {
                    '$gt': dt_utcnow()
                }
            },
            page=_page,
            page_size=_page_size,
            chain=_chain,
            contracts=_contracts,
            sort_field=_sort_field,
            sort_type=_sort_type,
        )

        return _result

    @staticmethod
    def get_user_nfts(user_id, params):
        _page = py_.get(params, 'page')
        _page_size = py_.get(params, 'page_size')
        _sort_field = py_.get(params, 'sort_field')
        _sort_type = py_.get(params, 'sort_type')
        _chain = py_.get(params, 'chain', None)
        _contracts = py_.get(params, 'contracts', None)

        _result = NFTsServices.get_nfts(
            page=_page,
            page_size=_page_size,
            chain=_chain,
            contracts=_contracts,
            sort_field=_sort_field,
            sort_type=_sort_type,
            user_id=user_id
        )

        return _result

    @staticmethod
    def check_owner_nft(user_address, nft_id):
        _nft = NsNftModel.find_one({
            '_id': nft_id,
            'owner': user_address.lower()
        })

        if not _nft:
            raise UserNotOwnNftEx

        return _nft

    @staticmethod
    def sell_nfts(form_data):
        _nft_id = py_.get(form_data, 'nft_id')
        _user_address = py_.get(form_data, 'user_address', '')

        _nft = NFTsServices.check_owner_nft(user_address=_user_address, nft_id=_nft_id)

        if NFTsServices.is_nft_on_market(item=_nft):
            raise NftIsOnMarketEx

        _buy_deadline = py_.get(form_data, 'buy_deadline')

        _deadline = dt_utcnow() + datetime.timedelta(days=_buy_deadline)

        _order_id = NsNftModel.sell_nft(sell_data={
            **form_data,
            'price': py_.to_string(py_.get(form_data, 'price')),
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

    @classmethod
    def mint_nfts(cls, user_id, form_data):
        _nft_contract = py_.get(form_data, 'nft_contract', '').lower()
        _nft_type = py_.get(form_data, 'nft_type')
        _amount = py_.get(form_data, 'amount', 0)
        _discount = py_.get(form_data, 'discount', 0)
        _is_whitelist_mint = py_.get(form_data, 'is_whitelist_mint', False)

        _log_data = {
            **form_data,
            'chain': py_.get(form_data, 'chain'),
            'price': py_.get(form_data, 'price'),
            'amount': _amount,
            'discount': _discount,
            'nft_type': _nft_type,
            'is_whitelist_mint': _is_whitelist_mint,
            'nft_contract': _nft_contract,
        }

        debug(_log_data)

        _inserted_data = DevMintOrdersModel.insert_one({
            'chain': py_.get(_log_data, 'chain'),
            'nft_contract': _nft_contract,
            'price': py_.get(_log_data, 'price'),
            'amount': py_.get(_log_data, 'amount'),
            'is_whitelist_mint': py_.get(_log_data, 'is_whitelist_mint'),
            'user_id': ObjectId(user_id),
            'is_minted': False,
            'data': _log_data,
            'created_by': 'dns-api:services:NFTsServices:mint_nfts'
        })

        _key = cls.get_mint_nfts_redis_key(mint_id=str(py_.get(_inserted_data, '_id')))
        _status = redis_cluster.set(_key, value='PENDING')
        worker.send_task(
            'worker.mint_nft_with_none_wallet',
            data={
                'mint_id': str(py_.get(_inserted_data, '_id')),
                'contract': _nft_contract,
                'type': py_.get(_log_data, 'nft_type'),
                'amount': py_.get(_log_data, 'amount'),
                'callback': str(py_.get(_inserted_data, '_id')),
            },
            chain=py_.get(_log_data, 'chain')
        )

        return {
            '_id': str(py_.get(_inserted_data, '_id'))
        }

    @staticmethod
    def cancel_sell_nfts(user_address, nft_id):
        if not bson.objectid.ObjectId.is_valid(nft_id):
            raise IsNotValidObjIdEx

        nft_id = bson.objectid.ObjectId(nft_id)

        _nft = NFTsServices.check_owner_nft(user_address=user_address, nft_id=nft_id)

        NsNftModel.cancel_sell_nft(nft_id=nft_id)

        OrdersModel.insert_one({
            'chain': py_.get(_nft, 'chain'),
            'token_id': py_.get(_nft, 'token_id'),
            'order_id': py_.get(_nft, 'order_id'),
            'price': py_.get(_nft, 'price'),
            'sender': py_.get(_nft, 'owner'),
            'receiver': None,
            'nft_id': nft_id,
            'action': MarketplaceAction.CANCEL_SELL,
            'data': _nft,
            'created_by': 'dns-api:services:NFTsServices:sell_user_nfts'
        })

        return {}

    @classmethod
    def get_mint_nfts_redis_key(cls, mint_id):
        return f'dns:mint_nft_without_wallet:{mint_id}'

    @classmethod
    def mint_nfts_status(cls, params):
        _id = py_.get(params, 'id')
        _key = cls.get_mint_nfts_redis_key(mint_id=_id)
        _status = redis_cluster.get(_key)
        return {
            'status': _status
        }
