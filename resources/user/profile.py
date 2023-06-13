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
from services import MNSServices
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

        _primary_domain = MNSServices.name(address=_address)

        return {
            'domains': _result,
            'primary_domain': _primary_domain
        }
