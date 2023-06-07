# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
import json
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv("DEBUG")
    PROJECT = "dns-api"
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SENTRY_DSN = os.getenv('SENTRY_DSN')

    # Setup db
    MONGO_URI = os.getenv('MONGO_URI')

    # Authentication
    AUTH_ADDRESS = os.getenv('AUTH_ADDRESS', '')
    AUTH_PRIVATE_KEY = os.getenv('AUTH_PRIVATE_KEY', '')
    TOKEN_EXPIRE_TIME = int(os.getenv('TOKEN_EXP_TIME', default='864000'))

    # Config celery worker
    CELERY_IMPORTS = ['tasks']
    ENABLE_UTC = True

    BROKER_USE_SSL = True
    BROKER_URL = os.getenv('BROKER_URL')
    CELERY_QUEUES = os.getenv('CELERY_QUEUES')

    CELERY_ROUTES = {
        'worker.sample_task': {'queue': 'dns-sample-queue'},
        'worker.task_register_domain': {'queue': 'dns-domain-queue'},
    }

    # Redis
    REDIS_CLUSTER = json.loads(os.getenv('REDIS_CLUSTER'))
    REDLOCK_REDIS = json.loads(os.getenv('REDLOCK_REDIS', '[]'))

    # Blockchain
    ETH_RPC_URI = os.getenv('ETH_RPC_URI')
    CHAIN_ID = int(os.getenv('CHAIN_ID'))

    WALLET_IAPI = os.getenv('WALLET_IAPI')
    CONFIRM_BLOCK = 1
