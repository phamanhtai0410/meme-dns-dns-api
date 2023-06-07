# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
from pydash import get
from connect import redis_cluster
from lib import ethereum, bsc, arbitrum, base_testnet, set_name_services
from lib.logger import debug
import bson.json_util
from worker import worker

SUPPORT_CHAIN = [ethereum, bsc, arbitrum, base_testnet]


@worker.task(name='worker.task_register_domain', rate_limit='1000/s')
def task_register_domain(event: str):
    try:
        _event = bson.json_util.loads(event)

        print(_event)

        return 'DONE - task_register_domain'
    except Exception as e:
        debug(f'ERROR - task_register_domain: {e}')
        return 'ERROR - task_register_domain'
