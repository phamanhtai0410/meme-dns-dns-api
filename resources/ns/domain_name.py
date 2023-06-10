# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource

from connect import security
from services.ns.ns_nfts import NsNFTsService
from schemas.ns.ns_nfts import NsNFTSchema


class NameServiceDomainNameResource(Resource):

    @security.http(
        response=NsNFTSchema(),
    )
    def get(self, domain_name):
        _result = NsNFTsService.get_nft_by_domain(domain_name=domain_name)

        return _result
