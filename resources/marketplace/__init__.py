# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.marketplace.nfts import MarketplaceNFTsResource
from resources.marketplace.nft_detail import MarketplaceNFTDetailResource
from resources.marketplace.sell_nft import SellNftResource

marketplace_resources = {
    '/nfts': MarketplaceNFTsResource,
    '/nfts/detail': MarketplaceNFTDetailResource,
    '/sell': SellNftResource,
    '/cancel_sell/<string:nft_id>': CancelSellNftResource,
}
