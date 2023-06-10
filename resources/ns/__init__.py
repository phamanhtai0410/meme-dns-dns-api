# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.ns.web3_name import NameServiceWeb3NamesResource
from resources.ns.wallet_address import NameServiceWalletAddressResource
from resources.ns.domain_name import NameServiceDomainNameResource


ns_resources = {
    '/web3_names': NameServiceWeb3NamesResource,
    '/wallet_address': NameServiceWalletAddressResource,
    '/<string:domain_name>': NameServiceDomainNameResource
}
