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


from schemas.ns.ns_nfts import NsNFTsRequestSchema, NsNFTsResponseSchema 
from schemas.request import RequestSchema
from services.ns.ns_nfts import NsNFTsService



class MarketplaceNFTsResource(Resource):

    @security.http(
        params=RequestSchema(),
        response=NsNFTsResponseSchema(),
        login_required=False
    )
    def get(self, params):
        _result = NsNFTsService.get_marketplace_nfts(params=params)

        return _result