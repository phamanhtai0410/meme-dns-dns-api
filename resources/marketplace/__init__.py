# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.marketplace.cancel_sell import CancelSellNftResource
from resources.marketplace.nfts import MarketplaceNFTsResource
from resources.marketplace.nft_detail import MarketplaceNFTDetailResource
from resources.marketplace.sell_nft import SellNftResource

marketplace_resources = {
    '/nfts': MarketplaceNFTsResource,
    '/nfts/detail': MarketplaceNFTDetailResource,
    '/sell': SellNftResource,
    '/cancel_sell/<string:user_address>/<string:nft_id>': CancelSellNftResource,
}
