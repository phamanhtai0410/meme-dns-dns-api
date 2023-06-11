# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.social.accounts_linked_with_domains import AccountsLinkedWithDomainsResource
from resources.social.check_account_linked_with_domain import CheckAccountLinkedWithDomainResource

social_resources = {
    '/accounts_linked/all': AccountsLinkedWithDomainsResource,
    '/check_account_linked': CheckAccountLinkedWithDomainResource,
}
