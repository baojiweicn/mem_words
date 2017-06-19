#!/usr/bin/env python
# encoding: utf-8

import os

DB_CONFIG = {
    'host':  os.environ.get('host', None),
    'user': os.environ.get('user', None),
    'password': os.environ.get('password', None),
    'port': os.environ.get('port', None),
    'database': 'youdao_dict' #os.environ.get('dbname', None)
}

REDIS_DB_CONFIG = {
    'host': 'localhost',
    'port': 6379
}

DEBUG = True
WORKERS = 2