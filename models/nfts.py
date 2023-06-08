# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
import pydash as py_

from lib import DaoModel
from lib.constants import NFT_CURRENT_ORDER_ID_KEY

class NftDao(DaoModel):

    def __init__(self, *args, **kwargs):
        super(NftDao, self).__init__(*args, **kwargs)

    def get_order_id(self):
        _current_id = self.redis.get(NFT_CURRENT_ORDER_ID_KEY)
        if not _current_id:
            return 1

        return int(_current_id) + 1

    def incr_order_id(self):
        self.redis.incr(NFT_CURRENT_ORDER_ID_KEY)

    def sell_nft(self, sell_data):
        _nft_id = py_.get(sell_data, 'nft_id')
        _buy_deadline = py_.get(sell_data, 'buy_deadline')        
        _price = py_.get(sell_data, 'price')       
        _order_id = self.get_order_id()

        self.update_one({
            '_id': _nft_id
        }, {
            'buy_deadline': _buy_deadline,
            'order_id': _order_id,
            'price': _price,
            'updated_by': 'dns-api:model:NftModel:sell_nft'
        })    

        self.incr_order_id()
        
        return _order_id
    
    def cancel_sell_nft(self, nft_id):
        self.update_one({
            '_id': nft_id
        }, {
            'buy_deadline': None, #NOTE: update buy_deadline to 0 will remove sell nft
            'updated_by': 'dns-api:model:NftModel:cancel_sell_nft'
        })
