import pydash as py_
from lib.utils import dt_utcnow

from models import NFTContractsModel, UsersModel, UsersTemplatesModel


class WebsiteExplorerService:
    @classmethod
    def mapping_website(cls, nft_contracts):
        _return_items = []
        if not nft_contracts:
            return _return_items
        
        _list_user = {}
        for _item in nft_contracts:
            _nft_contract_id = py_.get(_item, '_id')

            _user_template = UsersTemplatesModel.find_one({
                'contracts': _nft_contract_id
            })

            _user_id = py_.get(_item, 'user_id')

            if not _user_id in _list_user:
                _user = UsersModel.find_one({
                    '_id': _user_id
                })
                py_.set_(_list_user, _user_id, _user)
            
            _user = py_.get(_list_user, _user_id)

            _return_items.append({
                **_item,
                'website_domain': py_.get(_user_template, 'website_domain.0'),
                'full_domain': py_.get(_user_template, 'full_domain.0'),
                'user_template_id': py_.get(_user_template, '_id'),
                'user': _user
            })

        return _return_items


    @classmethod
    def get_list_deployed_website(cls, params):
        _page = py_.get(params, 'page')
        _page_size = py_.get(params, 'page_size')

        _result = NFTContractsModel.page(
            filter={
                'is_released': True
            },
            page=_page,
            page_size=_page_size,
            sort=-1,
            func_sort=lambda x: py_.get(x, 'created_time', dt_utcnow())
        )

        _items = WebsiteExplorerService.mapping_website(nft_contracts=py_.get(_result, 'items', []).copy())

        py_.set_(_result, 'items', _items)

        return _result
