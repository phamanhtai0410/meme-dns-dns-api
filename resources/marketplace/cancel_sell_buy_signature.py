# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get
from connect import security
from schemas.marketplace.sell_nft import SellNftsSchema, SellNftBuySignatureSchema, CancelSellNftBuySignatureSchema
from services.nft.nft import NFTsServices
from services.ns.ns_nfts import NsNFTsService


class CancelSellNftBySignatureResource(Resource):

    @security.http(
        form_data=CancelSellNftBuySignatureSchema(),
        # login_required=True
    )
    def post(self, form_data):
        _response = NsNFTsService.cancel_sell_nfts_by_signature(form_data=form_data)
        return _response
