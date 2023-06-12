# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.user.nfts import UserNFTsResource
from resources.user.profile import UserProfileResource

user_resources = {
    '/nfts': UserNFTsResource,
    '/profile': UserProfileResource
}
