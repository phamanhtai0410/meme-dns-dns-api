import pydash as py_
import web3
from exceptions.nft_contracts import NftContractNotFoundEx

from models import NFTContractsModel, UsersModel, UsersTemplatesModel
from lib.utils import dt_utcnow


class ContractsService:
    
    @staticmethod
    def get_by_contract_address(contract): 
        _result = NFTContractsModel.find_one({
            'contract': contract
        })

        if not _result:
            raise NftContractNotFoundEx

        return _result

