from ens import ENS
from pydash import get

from connect import web3_providers
from lib import ethereum

web3 = get(web3_providers, str(get(ethereum, 'id', '1')))
ns = ENS.from_web3(web3)


class ENSServices:

    @classmethod
    def get_eth_address_from_ens_name(cls, ens_name):
        return ns.address(ens_name)

    @classmethod
    def get_ens_name_from_eth_address(cls, address):
        if ns.name(web3.to_checksum_address(address)) is None:
            return []
        return [ns.name(web3.to_checksum_address(address))]

    @classmethod
    def get_owner_of_ens_name(cls, ens_name):
        return ns.owner(ens_name)
