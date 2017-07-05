#!/usr/bin/env python
# encoding: utf-8

import logging
from sanic import Sanic
from sanic.response import json, text
from sanic_openapi import swagger_blueprint, openapi_blueprint, doc
from config import DEBUG, WORKERS, DB_CONFIG
from common.db import BaseConnection
from common.client import Client
from common.server import app
from views import youdao_bp

logger = logging.getLogger('sanic')
# add blueprint
app.blueprint(youdao_bp)
app.static('/', './template')

@app.route("/")
async def test(request):
    return text('Hello world!')

app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'Visit API'
app.config.API_DESCRIPTION = 'Visit API'
app.config.API_TERMS_OF_SERVICE = 'Use with caution!'
app.config.API_PRODUCES_CONTENT_TYPES = ['application/json']
app.config.API_CONTACT_EMAIL = 'it@baojiwei.cn'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=51888, debug=DEBUG)
