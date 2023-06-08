import pydash as py_
from lib.utils import dt_utcnow

from exceptions.nfts import NftNotFoundEx
from exceptions.requests import IsNotValidObjIdEx

from models import NsNftModel


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