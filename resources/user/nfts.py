# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from datetime import datetime
from random import randrange

from flask_restful import Resource
from pydash import get
from flask import request

from connect import security
from lib import dt_utcnow


from schemas.ns.ns_nfts import NsNFTsRequestSchema, NsNFTsResponseSchema 
from services.ns.ns_nfts import NsNFTsService


class UserNFTsResource(Resource):

    @security.http(
        params=NsNFTsRequestSchema(),
        response=NsNFTsResponseSchema(),
        login_required=False
    )
    def get(self, params):
        _result = NsNFTsService.get_user_list(params=params)

        return _result
