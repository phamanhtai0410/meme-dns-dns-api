# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from datetime import datetime
from random import randrange

from flask_restful import Resource

from connect import security
from schemas.marketplace.nft_detail import MarketplaceNFTDetailRequestSchema
from schemas.ns.ns_nfts import NsNFTSchema
from services.ns.ns_nfts import NsNFTsService


class MarketplaceNFTDetailResource(Resource):

    @security.http(
        params=MarketplaceNFTDetailRequestSchema(),
        response=NsNFTSchema(),
        # login_required=True
    )
    def get(self, params):

        _result = NsNFTsService.get_by_token_id(params=params)

        return _result
