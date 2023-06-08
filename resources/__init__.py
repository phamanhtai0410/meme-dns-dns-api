# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from resources.health_check import HealthCheck
from resources.hello import HelloWorld
# from resources.iapi import iapi_resources
from resources.user import user_resources
from resources.ns import ns_resources
from resources.marketplace import marketplace_resources
from resources.smc import smc_resources

api_resources = {
    '/hello': HelloWorld,
    '/common/health_check': HealthCheck,
    # **{f'/iapi{k}': val for k, val in iapi_resources.items()},
    **{f'/user{k}': val for k, val in user_resources.items()},
    **{f'/ns{k}': val for k, val in ns_resources.items()},
    **{f'/marketplace{k}': val for k, val in marketplace_resources.items()},
    **{f'/smc{k}': val for k, val in smc_resources.items()},
}
