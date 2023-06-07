# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from datetime import datetime
from random import randrange

from flask_restful import Resource
from pydash import get
from flask import request

from connect import security
from lib import dt_utcnow


# from schemas import NFTsRequestSchema, NFTsResponseSchema
# from services import NFTsServices


class UserNFTsResource(Resource):

    @security.http(
        # params=NFTsRequestSchema(),
        # response=NFTsResponseSchema(),
        # login_required=True
    )
    def get(self):
        # _contracts = request.args.getlist('contract[]', str)
        #
        # _response = NFTsServices.get_user_nfts(user_id=get(login_info, 'user._id'), params={
        #     **params,
        #     'contracts': _contracts
        # })

        _result = []
        i = 0
        while i < 15:
            _num = randrange(999)
            i += 1
            now = datetime.now()
            _expires = int(datetime.timestamp(now)) + _num * 2
            _buy_deadline = int(datetime.timestamp(now)) + _num * 10
            _base_cost = 0.00000000025056 + _num / (10 ** 9)
            _price = _num / 10
            _token_id = "15022736803242841036530282932891759087964788378666743883866444704004022938799".replace(str(randrange(9)), str(randrange(9)))
            _domain_name = 'test123456789.meme'.replace(str(randrange(9)), str(randrange(9)))
            _result.append({
                "token_id": _token_id,
                "domain_name": _domain_name,
                "owner": "0x5d12ffaf4ab3d70b5c3941dd6a29fc6fc4415eb4",
                "expires": _expires,
                "label_hash": "0x6465763264657631313132322e6d656d65000000000000000000000000000000",
                "base_cost": '{:.15f}'.format(_base_cost),
                "metadata_link": "https://static.esollabs.com/nft/metadata/0xaddc8a6848f828f9f3d5e0bd19b02f17a9bc693e/187087.json",
                "buy_deadline": _buy_deadline,
                "price": _price,
                "image_url": "https://static.esollabs.com/scanhub/2023/04/16/Aprh25M1681658721s_DALLE_2023-04-16_22.10.12_-_3D_render_of_a_cute_tropical_fish_in_an_aquarium_on_a_Moon_background_fish_multiple_color_digital_art_.png"
            })

        return {
            'items': _result,
            'page': 1,
            'page_size': 20,
            'num_of_page': 1
        }
