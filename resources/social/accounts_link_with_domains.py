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


from schemas.social.accounts_link_with_domains import AccountsLinkWithDomainsRequestSchema, \
    AccountsLinkWithDomainsResponseSchema


class AccountsLinkWithDomainsResource(Resource):

    @security.http(
        params=AccountsLinkWithDomainsRequestSchema(),
        response=AccountsLinkWithDomainsResponseSchema(),
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
