import requests
from pydash import get

from lib import BadRequest, NotFound


class BaseNameServices:

    @classmethod
    def get_address_from_domain(cls, domain: str):
        _url = f'https://testnet-api.basename.app/v1/wallet-addresses/{domain}'
        _res = requests.get(url=_url)

        if _res.status_code != 200:
            raise NotFound(msg='Services error!')

        _data = _res.json()

        return get(_data, 'wallet', '').lower()

    @classmethod
    def get_domain_from_address(cls, address: str):
        _url = f'https://testnet-api.basename.app/v1/web3-names/{address}'
        _res = requests.get(url=_url)

        if _res.status_code != 200:
            raise NotFound(msg='Services error!')

        _data = _res.json()
        _result = []

        for _item in _data:
            _bns = get(_item, 'bns', '')
            if _bns and _bns not in _result:
                _result.append(_bns)

        return _result
