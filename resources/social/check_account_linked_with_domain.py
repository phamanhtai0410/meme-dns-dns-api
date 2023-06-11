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
from schemas.social.check_account_linked_with_domain import CheckAccountLinkedWithDomainRequestSchema


class CheckAccountLinkedWithDomainResource(Resource):

    @security.http(
        form_data=CheckAccountLinkedWithDomainRequestSchema(),
        # response=CheckAccountLinkedWithDomainResponseSchema(),
        # login_required=True
    )
    def post(self, form_data):
        # _page = get(params, 'page')
        # _page_size = get(params, 'page_size')
        _social_name = get(form_data, 'social_name')
        _social_account = get(form_data, 'social_account')

        _result = SocialsModel.find_one(
            filter={
                'social_name': _social_name,
                'social_account': _social_account
            }
        )

        return {
            'is_linked': False if _result is None else True
        }
