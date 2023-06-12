# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get

from connect import security
from schemas.user.profile import UserProfileRequestSchema
from services.ns.ns_nfts import NsNFTsService


class UserProfileResource(Resource):

    @security.http(
        params=UserProfileRequestSchema(),
        # response=UserProfileResponseSchema(),
        login_required=False
    )
    def get(self, params):
        _address = get(params, 'owner', '').lower()
        _result = NsNFTsService.get_domains(address=_address)

        return {
            'domains': _result
        }
