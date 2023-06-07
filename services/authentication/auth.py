# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
import string
from datetime import timedelta

import jwt
# from bcrypt import checkpw
from pydash import get

from config import Config
from connect import web3_providers, redis_cluster
from enums.user import SignInProviders
from helper.account.account import AccountsHelpers
from helper.wallet.wallet import WalletsHelpers
from lib import BadRequest
from lib.logger import debug
from lib.security import auth_token_key
from lib.utils import random_str, dt_utcnow
from models import UsersModel, AccountsModel
from services.social.google import GoogleServices
from tasks import task_save_user, task_save_session


with open('conf/keys/private.key') as f:
    TOKEN_KEY = f.read()


class AuthServices:

    @classmethod
    def _gen_nonce(cls):
        return random_str(size=8, chars=string.digits)

    @classmethod
    def _gen_access_token(cls, session: dict) -> str:
        _subdomain = get(session, 'subdomain')

        _key = auth_token_key(user=get(session, 'user._id'), subdomain=_subdomain)
        _payload = {
            'payload': session,
            'iat': dt_utcnow(),  # init time
            'exp': dt_utcnow() + timedelta(seconds=Config.TOKEN_EXPIRE_TIME),
        }
        _access_token = jwt.encode(_payload, TOKEN_KEY, algorithm='RS256')

        # save
        redis_cluster.setex(name=_key, time=Config.TOKEN_EXPIRE_TIME, value=_access_token)

        return _access_token

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

        _web3 = get(web3_providers, str(chain))

        _nonce = get(session, 'nonce')
        _msg, _nonce = cls.get_validate_msg(nonce=_nonce)

        _real_public_address = _web3.recover_address_from_msg_sign(msg=_msg, signature=signature)

        if not _real_public_address.lower() == public_address:
            return False, None
        _user = WalletsHelpers.user_of(
            address=public_address,
            with_upsert=True
        )
        # Update user and create if not exist
        task_save_user.delay(
            user=str(_user['_id']),
            # data=session,
            wallet={
                'public_address': public_address
            },
            is_login=True)

        _access_token = cls._gen_access_token(session={
            'public_address': public_address,
            'nonce': _nonce,
            "device_id": get(session, 'device_id'),
            "xrip": get(session, 'xrip'),
            'user': {
                '_id': str(get(_user, '_id')),
                'username': get(_user, 'username'),
                'avatar': get(_user, 'avatar'),
                'roles': get(_user, 'roles'),
            },
            'provider': SignInProviders.BLOCKCHAIN,
            'chain_id': get(session, 'chain_id'),
            'subdomain': get(session, 'subdomain')
        })
        session['user'] = {
            '_id': str(get(_user, '_id')),
            'username': get(_user, 'username'),
            'avatar': get(_user, 'avatar'),
            'roles': get(_user, 'roles'),
        }
        del session['signature']

        # Record session
        task_save_session.delay({
            **session,
            'access_token': _access_token,
            'provider': SignInProviders.BLOCKCHAIN
        })

        return _access_token, _nonce

    @classmethod
    def connect_google(cls, token: str, session: dict):
        _info = GoogleServices.verify(token)

        if not _info:
            raise BadRequest(msg='Invalid params.', errors=['Google token invalid.'])

        _email = get(_info, 'email')
        _display_name = get(_info, 'display_name')
        _photo_url = get(_info, 'photo_url')

        debug('connect google', _email, _display_name)

        _user = AccountsHelpers.user_of(email=_email)
        if not _user:
            _user = UsersModel.insert_one({
                'username': _display_name,
                'avatar': _photo_url,
                'last_login': dt_utcnow(),
                'public_address': '',
                'roles': [],
                'created_time': dt_utcnow(),
                'updated_time': dt_utcnow(),
                'created_by': 'inz-api:services:authentication:auth:connect_google',
                'updated_by': ''
            })
            print('_info **** ', _info.__dict__.get('_data'))

            AccountsModel.insert_one({
                'email': _email,
                'provider': SignInProviders.GOOGLE,
                'user': _user['_id'],
                'active': True,
                'info': _info.__dict__.get('_data'),
                'created_time': dt_utcnow(),
                'updated_time': dt_utcnow(),
                'created_by': 'inz-api:services:authentication:auth:connect_google',
                'updated_by': ''
            })

        _access_token = cls._gen_access_token(session={
            'public_address': '',
            'nonce': token,
            'device_id': '',
            'xrip': session.get('xrip', ''),
            'user': {
                '_id': str(get(_user, '_id')),
                'username': get(_user, 'username'),
                'avatar': get(_user, 'avatar'),
                'roles': get(_user, 'roles'),
            },
            'provider': SignInProviders.GOOGLE,
            'subdomain': get(session, 'subdomain')
        })

        # Record session
        task_save_session.delay({
            **session,
            'public_address': '',
            'nonce': '',
            'user': {
                '_id': str(get(_user, '_id')),
                'username': get(_user, 'username'),
                'avatar': get(_user, 'avatar'),
                'roles': get(_user, 'roles'),
            },
            'access_token': _access_token,
            'provider': SignInProviders.GOOGLE
        })

        return _access_token

    # @staticmethod
    # def auth(username, password):
    #     _user = UserModel.find_one({
    #         'auth_username': username
    #     }, with_cache=False)
    #     if _user and get(_user, 'password'):
    #         if checkpw(password.encode('utf8'), _user.get('password').encode('utf8')):
    #             return _user
    #     return None
    #
    # @classmethod
    # def admin(cls, username, password, session):
    #     _user = cls.auth(
    #         username,
    #         password=password
    #     )
    #     if not _user:
    #         raise BadRequest("User not found")
    #     _access_token = cls._gen_access_token(user=str(_user['_id']), session={
    #         'public_address': '',
    #         'nonce': 'admin',
    #         "device_id": session.get('device_id', ''),
    #         "xrip": session.get('xrip', ''),
    #         'user': str(_user['_id']),
    #         'subdomain': get(session, 'subdomain')
    #     })
    #
    #     # Record session
    #     auth_worker.save_session.delay({
    #         **session,
    #         'access_token': _access_token,
    #         'user': str(_user['_id'])
    #     })
    #     return _access_token
