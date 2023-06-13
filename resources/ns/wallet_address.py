# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get

from connect import security
from schemas.ns.wallet_address import NameServiceWalletAddressRequestSchema
from services import MNSServices


class NameServiceWalletAddressResource(Resource):

    @security.http(
        params=NameServiceWalletAddressRequestSchema(),
        # response=NFTsResponseSchema(),
        # login_required=True
    )
    def get(self, params):
        _web3_name = get(params, 'web3_name', '').lower()

        _address = MNSServices.address(name=_web3_name)

        return {
            'mns': _address
        }
