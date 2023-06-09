# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get
from connect import security
from schemas.marketplace.sell_nft import SellNftsSchema, SellNftBuySignatureSchema
from services.nft.nft import NFTsServices
from services.ns.ns_nfts import NsNFTsService


class SellNftBySignatureResource(Resource):

    @security.http(
        form_data=SellNftBuySignatureSchema(),
        # login_required=True
    )
    def post(self, form_data):
        _response = NsNFTsService.sell_nfts_by_signature(form_data=form_data)
        return _response
