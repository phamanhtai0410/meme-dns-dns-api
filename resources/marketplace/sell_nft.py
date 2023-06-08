# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get
from connect import security
from schemas.marketplace.sell_nft import SellNftsSchema
from services.nft.nft import NFTsServices


class SellNftResource(Resource):

    @security.http(
        form_data=SellNftsSchema(),
        # login_required=True
    )
    def post(self, form_data):
        _response = NFTsServices.sell_nfts(form_data=form_data)
        return _response
