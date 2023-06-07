import requests
from pydash import get

from lib import BadRequest, NotFound


class SpaceIDServices:

    @classmethod
    def get_address_from_domain(cls, tld: str, domain: str):
        _url = f'https://api.prd.space.id/v1/getAddress?tld={tld}&domain={domain}'
        _res = requests.get(url=_url)

        if _res.status_code != 200:
            raise NotFound(msg='Services error!')

        _data = _res.json()
        if get(_data, 'code') != 0:
            raise BadRequest(msg=get(_data, 'msg'))

        return get(_data, 'address', '').lower()

    @classmethod
    def get_domain_from_address(cls, tld: str, address: str):
        _url = f'https://api.prd.space.id/v1/getName?tld={tld}&address={address}'
        _res = requests.get(url=_url)

        if _res.status_code != 200:
            raise NotFound(msg='Services error!')

        _data = _res.json()
        if get(_data, 'code') != 0:
            raise BadRequest(msg=get(_data, 'msg'))

        if get(_data, 'name') is None:
            return []
        return [get(_data, 'name')]
