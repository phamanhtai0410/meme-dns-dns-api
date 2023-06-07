# -*- coding: utf-8 -*-
"""
   Description:
        -
        -
"""
__models__ = ['OrderModel']

from connect import connect_db, redis_cluster
from lib import DaoModel
from models.order import OrderDao

# TemplatesModel = DaoModel(col=connect_db.db.templates, redis=redis_cluster)
