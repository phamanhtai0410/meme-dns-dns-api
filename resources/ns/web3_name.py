# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get

from connect import security
from schemas.ns.web3_name import NameServiceWeb3NamesRequestSchema
from services import MNSServices


class NameServiceWeb3NamesResource(Resource):

    @security.http(
        params=NameServiceWeb3NamesRequestSchema(),
    )
    def get(self, params):
        _wallet_address = get(params, 'wallet_address', '').lower()

        _domain = MNSServices.name(address=_wallet_address)

        return {
            'domain': _domain
        }
