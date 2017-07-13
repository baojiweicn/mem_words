#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sanic import Sanic
from sanic.response import json, text
from sanic_openapi import swagger_blueprint, openapi_blueprint

from config import DB_CONFIG, TEMPLATE_PATH, REDIS_DB_CONFIG
from common.db import BaseConnection
from common.client import Client
from jinja2 import Environment, FileSystemLoader
from sanic_session import RedisSessionInterface
import asyncio_redis

logger = logging.getLogger('sanic')
# make app
app = Sanic(__name__)

class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(host=REDIS_DB_CONFIG['host'], port=REDIS_DB_CONFIG['port'], poolsize=10)
        return self._pool

redis = Redis()

session_interface = RedisSessionInterface(redis.get_redis_pool)

app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.listener('before_server_start')
async def before_srver_start(app, loop):
    app.db = await BaseConnection(loop=loop).init(DB_CONFIG=DB_CONFIG)
    app.client =  Client(loop=loop)
    app.env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), enable_async=True)

@app.listener('before_server_stop')
async def before_server_stop(app, loop):
    app.client.close()

@app.middleware('request')
async def cros(request):
    await session_interface.open(request)
    if request.method == 'OPTIONS':
        headers = {'Access-Control-Allow-Origin': '*',
                   'Access-Control-Allow-Headers': 'Content-Type',
                   'Access-Control-Allow-Method': 'POST, PUT, DELETE'}
        return json({'message': 'Hello World'}, headers=headers)

@app.middleware('response')
async def cors_res(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Method"] = "POST, PUT, DELETE"
    await session_interface.save(request, response)

