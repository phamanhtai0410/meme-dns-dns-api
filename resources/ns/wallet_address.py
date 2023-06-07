# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource

from connect import security
from schemas.ns.wallet_address import NameServiceWalletAddressRequestSchema


class NameServiceWalletAddressResource(Resource):

    @security.http(
        params=NameServiceWalletAddressRequestSchema(),
        # response=NFTsResponseSchema(),
        # login_required=True
    )
    def get(self, params):
        return {
            "_id": "64672990bb6989fad32ad20b",
            "bns": "mockup.meme",
            "wallet": "0x0Db2d712339Ca567d4660F19E0788701129b5571",
            "bnsHashName": "0x183dc2acbb3dc2dbacc062d8c72c3644b4edf934164d13b4c1d44f05e1917393",
            "label": "mockup",
            "tld": "meme",
            "__v": 0
        }
