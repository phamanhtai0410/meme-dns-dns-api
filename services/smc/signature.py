import string
import uuid
import pydash as py_
from eth_account import Account
from eth_account.messages import encode_structured_data
from config import Config

from exceptions.nft_contracts import NftContractNotFoundEx
from exceptions.nfts import NftIsNotOnMarketEx, CurrencyTokenNotExceptEx
from exceptions.trade_nft import NftTradeOwnerAddressCanNotEqualToAddress
from helper.signature import SignatureHelper
from lib.enums.signature import SignatureType
from lib.utils import random_str
from models import NsNftModel, NFTContractsModel, SignatureLogModel, CryptoCurrenciesModel
from services import NFTsServices

from connect import web3_providers


class SMCSignatureService:
    @classmethod
    def _gen_nonce(cls):
        return random_str(size=8, chars=string.digits)

    @classmethod
    def get_validate_msg(cls, nonce=None):
        if not nonce:
            nonce = cls._gen_nonce()

        return f"I am signing to Innovaz with nonce: {nonce}", nonce

    @classmethod
    def verify(cls, signature: str, public_address: str, session: dict, chain: int):
        """
            - Verify signature of session
        """

        _web3 = py_.get(web3_providers, str(chain))

        _nonce = py_.get(session, 'nonce')
        _msg, _nonce = cls.get_validate_msg(nonce=_nonce)

        _real_public_address = _web3.recover_address_from_msg_sign(
            msg=_msg, signature=signature)

        if not _real_public_address.lower() == public_address:
            return False, None

        return _real_public_address, _nonce

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
            'token_id': py_.get(_nft, 'token_id'),
            'price': py_.get(_nft, 'price'),
            'owner_address': _owner_address,
            'standard': 1,
            'currency_address': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
            'currency_decimal': 18
        }

        _signature_data = SignatureHelper.generate_buy_nft_signature(
            data=_sign_data)

        _log_id = str(uuid.uuid4())

        SignatureLogModel.insert_one({
            **_sign_data,
            'log_id': _log_id,
            'signature': py_.get(_signature_data, 'signature'),
            'deadline': py_.get(_signature_data, 'deadline'),
            'type': SignatureType.BUY,
            'created_by': 'dns-api:SMCSignatureService:SM:create_buy_nft_signature'
        })

        return _signature_data
