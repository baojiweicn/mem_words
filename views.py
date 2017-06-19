#!/usr/bin/env python
# encoding: utf-8

import logging
from sanic import  Blueprint, response
from sanic.response import json, text
from sanic_openapi import doc
import ujson
from common.utils import jsonify, insert_sql, select_sql, update_sql
import datetime
from bs4 import  BeautifulSoup
import ujson
import pickle

logger = logging.getLogger('sanic')
youdao_bp = Blueprint('youdao', url_prefix='youdao')

async def create_audio(data):
    timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    #主要是懒,@todo写道config.py里面
    path = 'audio/'+str(timestamp).split('.')[0]+'.wav'
    fs = open(path, 'wb')
    fs.write(data)
    fs.close()
    return path


@youdao_bp.route('/audio/<word:string>', methods=['GET'])
async def get_word_audio(request, word):
    records = None
    async with request.app.db.acquire() as cur:
        records = await cur.fetch("select * from word_audio where word = '%s'"%word)
    if records:
        audio_path = records[0]['audio_path']
        async def streaming_fn(response):
            fs = open(audio_path,'rb')
            data = fs.read()
            response.write(data)
        return response.stream(streaming_fn,content_type='audio/mpeg')
    else:
        cli = request.app.client.cli
        #主要是懒,@todo写道config.py里面
        url = "http://dict.youdao.com/dictvoice?audio=" + word
        async with cli.get(url) as res:
            if res.status == 200:
                data = await res.read()
                async def streaming_fn(response):
                    response.write(data)
                    path = await create_audio(data)
                    async with request.app.db as cur:
                        await cur.fetch("INSERT INTO word_audio (create_time,word,audio_path) VALUES (current_timestamp,'%s','%s')" %(word,path))
                return response.stream(streaming_fn,content_type='audio/mpeg')
    return json({},status = 400)

@youdao_bp.route('/translate/<word:string>', methods=['GET'])
async def get_word_translate(request, word):
    records = None
    async with request.app.db.acquire() as cur:
        records = await cur.fetch("select * from word_translate where word='%s'"%word)
    if records:
        res = ujson.loads(records[0]['translate'])
        return json(res)
    else:
        cli = request.app.client.cli
        #直接写url主要是懒
        #主要是懒,@todo写道config.py里面
        url = "http://dict.youdao.com/search?keyfrom=dict.top&q="+word
        async with cli.get(url) as res:
            if res.status == 200:
                data = await res.text()
                res = await parse_html(data,word)
                async with request.app.db as cur:
                    #return json(res)
                    json_data = ujson.dumps(res)
                    json_data = json_data.replace("'","''")
                    await cur.fetch( """INSERT INTO word_translate (create_time,word,translate) VALUES (current_timestamp,'%s','%s')"""%(word,json_data))
                    #await cur.fetch( """INSERT INTO word_translate (create_time,word,translate) VALUES (current_timestamp,'%s',)"""%(word,ujson.dumps(res)))
                    return json(res)
    return json({},status = 400)

async def parse_html(html,word):
    """
    解析web版有道的网页
    :param html:网页内容
    :return:result
    """
    soup = BeautifulSoup(html, "lxml")
    root = soup.find(id='results-contents')

    # query 搜索的关键字
    keyword = root.find(class_='keyword')
    result = {}
    if not keyword:
        result['query'] = word
    else:
        result['query'] = str(keyword.string)

    # 基本解释
    basic = root.find(id='phrsListTab')
    if basic:
        trans = basic.find(class_='trans-container')
        if trans:
            result['basic'] = {}
            result['basic']['explains'] = [str(tran.string) for tran in trans.find_all('li')]
            # 中文
            if len(result['basic']['explains']) == 0:
                exp = trans.find(class_='wordGroup').stripped_strings
                result['basic']['explains'].append(' '.join(exp))

                # 音标
            phons = basic(class_='phonetic', limit=2)
            if len(phons) == 2:
                result['basic']['uk-phonetic'], result['basic']['us-phonetic'] = \
                    [str(p.string)[1:-1] for p in phons]
            elif len(phons) == 1:
                result['basic']['phonetic'] = str(phons[0].string)[1:-1]

    # 翻译
    if 'basic' not in result:
        result['translation'] = get_translation(word)

    # 网络释义(短语)
    web = root.find(id='webPhrase')
    if web:
        result['web'] = [
            {
                'key': str(wordgroup.find(class_='search-js').string).strip(),
                'value': [v.strip() for v in str(wordgroup.find('span').next_sibling).split(';')]
            } for wordgroup in web.find_all(class_='wordGroup', limit=4)
        ]
    return result
