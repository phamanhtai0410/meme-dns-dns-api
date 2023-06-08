# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.marketplace.nfts import MarketplaceNFTsResource
from resources.marketplace.nft_detail import MarketplaceNFTDetailResource

marketplace_resources = {
    '/nfts': MarketplaceNFTsResource,
    '/nfts/detail': MarketplaceNFTDetailResource
}
