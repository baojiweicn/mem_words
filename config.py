#!/usr/bin/env python
# encoding: utf-8

import os

DB_CONFIG = {
    'host':  os.environ.get('host', None),
    'user': os.environ.get('user', None),
    'password': os.environ.get('password', None),
    'port': os.environ.get('port', None),
    'database': os.environ.get('dbname', None)
}
TEMPLATE_PATH = 'template/html'

REDIS_DB_CONFIG = {
    'host': 'redis',
    'port': 6379
}

DEBUG = True
WORKERS = 2
