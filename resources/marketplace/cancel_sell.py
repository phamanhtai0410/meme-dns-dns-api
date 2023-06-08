# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get

from connect import security
from services.nft.nft import NFTsServices


class CancelSellNftResource(Resource):

    @security.http(
        # login_required=True
    )
    def put(self, user_address, nft_id):
        _response = NFTsServices.cancel_sell_nfts(user_address=user_address, nft_id=nft_id)
        return _response
