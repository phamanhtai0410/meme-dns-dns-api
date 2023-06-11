# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
__models__ = ['OrdersModel', 'SignatureLogModel']

from config import Config
from connect import connect_db, redis_cluster
from lib import DaoModel
from models.order import OrderDao
from models.signature import SignatureDao
from models.nfts import NftDao

NFTContractsModel = DaoModel(col=connect_db.db.nft_contracts, redis=redis_cluster)
CryptoCurrenciesModel = DaoModel(col=connect_db.db.crypto_currencies, redis=redis_cluster)

SocialsModel = OrderDao(col=connect_db.db.socials, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)

OrdersModel = OrderDao(col=connect_db.db.orders, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)

NsNftModel = NftDao(col=connect_db.db.ns_nfts, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)
TxLogsModel = DaoModel(col=connect_db.db.tx_logs, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)

DevMintOrdersModel = OrderDao(col=connect_db.db.dev_mint_orders, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)
SignatureLogModel = SignatureDao(col=connect_db.db.signature_log, redis=redis_cluster, project=Config.PROJECT, broker=Config.BROKER_URL)

