# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from flask_restful import Resource
from pydash import get

from connect import security
from models import SocialsModel


from schemas.social.accounts_linked_with_domains import AccountsLinkedWithDomainsRequestSchema, \
    AccountsLinkedWithDomainsResponseSchema


class AccountsLinkedWithDomainsResource(Resource):

    @security.http(
        params=AccountsLinkedWithDomainsRequestSchema(),
        response=AccountsLinkedWithDomainsResponseSchema(),
        # login_required=True
    )
    def get(self, params):
        # _page = get(params, 'page')
        # _page_size = get(params, 'page_size')
        _social_name = get(params, 'social_name')

        _results = SocialsModel.find(filter={'social_name': _social_name})

        return {
            'items': list(_results)
        }
