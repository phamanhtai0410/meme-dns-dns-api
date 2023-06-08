import uuid
import pydash as py_

from exceptions.nft_contracts import NftContractNotFoundEx
from exceptions.nfts import NftIsNotOnMarketEx, CurrencyTokenNotExceptEx
from exceptions.trade_nft import NftTradeOwnerAddressCanNotEqualToAddress
from helper.signature import SignatureHelper
from lib.enums.signature import SignatureType
from models import NsNftModel, NFTContractsModel, SignatureLogModel, CryptoCurrenciesModel
from services.nft.nft import NFTsServices


class SMCSignatureService:
    @staticmethod
    def create_buy_nft_signature(form_data):

        _chain_id = py_.get(form_data, 'chain_id')
        _nft_id = py_.get(form_data, 'nft_id')
        _to_address = py_.get(form_data, 'to_address')

        _nft = NsNftModel.find_one({
            '_id': _nft_id
        })
        if not _nft or not NFTsServices.is_nft_on_market(item=_nft):
            raise NftIsNotOnMarketEx

        _owner_address = py_.get(_nft, 'owner')

        if _owner_address.lower() == _to_address.lower():
            raise NftTradeOwnerAddressCanNotEqualToAddress

        _sign_data = {
            'chain_id': _chain_id,
            'order_id': py_.get(_nft, 'order_id'),
            'to_address': _to_address,
            'nft_address': py_.get(_nft, 'contract'),
            'token_id': py_.to_integer(py_.get(_nft, 'token_id')),
            'price': py_.get(_nft, 'price'),
            'owner_address': _owner_address,
            'standard': 1,
            'currency_address': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
            'currency_decimal': 18
        }

        _signature_data = SignatureHelper.generate_buy_nft_signature(data=_sign_data)

        _log_id = str(uuid.uuid4())

        SignatureLogModel.insert_one({
            **_sign_data,
            'log_id': _log_id,
            'signature': py_.get(_signature_data, 'signature'),
            'deadline': py_.get(_signature_data, 'deadline'),
            'type': SignatureType.BUY,
            'created_by': 'dns-api:SMCSignatureService:SM:create_buy_nft_signature'
        }, worker=True)

        return _signature_data
