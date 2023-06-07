# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource

from connect import security
from schemas.ns.web3_name import NameServiceWeb3NamesRequestSchema


class NameServiceWeb3NamesResource(Resource):

    @security.http(
        params=NameServiceWeb3NamesRequestSchema(),
        # response=NFTsResponseSchema(),
        # login_required=True
    )
    def get(self, params):

        return {
            'items': [
                {
                    "_id": "64672990bb6989fad32ad20b",
                    "bns": "mockup.meme",
                    "wallet": "0x0Db2d712339Ca567d4660F19E5788401139b1571",
                    "bnsHashName": "0x183dc2acbb3dc2dbacc062d8c72c3644b4edf934164d13b4c1d44f05e1917393",
                    "label": "mockup",
                    "tld": "meme"
                }
            ],
            'page': 1,
            'page_size': 20,
            'num_of_page': 1
        }
