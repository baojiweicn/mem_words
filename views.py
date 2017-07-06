#!/usr/bin/env python
# encoding: utf-8

import logging
from sanic import  Blueprint, response
from sanic.response import json, text, html, redirect
from sanic_openapi import doc
import ujson
from common.utils import jsonify, insert_sql, select_sql, update_sql
import datetime
from bs4 import  BeautifulSoup
import ujson
import pickle
import re
import hashlib
import xml.etree.ElementTree as ET
import datetime
import time
import redis

logger = logging.getLogger('sanic')
youdao_bp = Blueprint('youdao', url_prefix='words')
review_time_list = {
    '0': datetime.timedelta(minutes=5),
    '1': datetime.timedelta(hours=1),
    '2': datetime.timedelta(hours=3),
    '3': datetime.timedelta(hours=6),
    '4': datetime.timedelta(hours=12),
    '5': datetime.timedelta(days=1),
    '6': datetime.timedelta(days=2),
    '7': datetime.timedelta(days=3),
    '8': datetime.timedelta(days=5),
    '9': datetime.timedelta(days=10),
    '10': datetime.timedelta(days=20),
    '11': datetime.timedelta(days=30)
}

async def create_audio(data):
    timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    #主要是懒,@todo写道config.py里面
    path = 'audio/'+str(timestamp*10000).split('.')[0]+'.wav'
    fs = open(path, 'wb')
    fs.write(data)
    fs.close()
    return path


@youdao_bp.route('/audios/<word:string>', methods=['GET'])
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
                path = await create_audio(data)
                async with request.app.db as cur:
                     await cur.fetch("INSERT INTO word_audio (create_time,word,audio_path) VALUES (current_timestamp,'%s','%s')" %(word,path))
                async def streaming_fn(response):
                    response.write(data)
                return response.stream(streaming_fn,content_type='audio/mpeg')
    return json({},status = 400)

@youdao_bp.route('/translates/<word:string>', methods=['GET'])
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
                res = await parse_html(request,data,word)
                async with request.app.db as cur:
                    #return json(res)
                    json_data = ujson.dumps(res)
                    json_data = json_data.replace("'","''")
                    await cur.fetch( """INSERT INTO word_translate (create_time,word,translate) VALUES (current_timestamp,'%s','%s')"""%(word,json_data))
                    #await cur.fetch( """INSERT INTO word_translate (create_time,word,translate) VALUES (current_timestamp,'%s',)"""%(word,ujson.dumps(res)))
                    return json(res)
    return json({},status = 400)

@youdao_bp.route('/search/<word:string>', methods=['GET'])
async def get_word(request, word):
    res = await get_word_translate(request, word)
    audio = await get_word_audio(request, word)
    return res

@youdao_bp.route('/users',methods=['POST'])
async def add_user(request,fromu=None):
    data = {}
    try:
        if not fromu:
            data = ujson.loads(request.body)
        else:
            data = {"username":fromu}
    except:
        return json({},status = 400)
    if data.get('username') and len(data.get('username'))>5 :
        async with request.app.db.acquire() as cur:
            records = await cur.fetch("select * from users where username='%s'"%data.get('username'))
            if records:
                request['session']['user_id'] = records[0]['id']
                return json(jsonify(records)[0])
            else:
                sql = """insert into users (create_time,username,name,wechat_user) values
                (current_timestamp,'%s','%s','%s') returning *"""
                user_info = (data.get('username'),data.get('name') if data.get('name') else data.get('username'),data.get('wechat_user') if data.get('wechat_user') else 'NULL')
                records = await cur.fetch(sql%user_info)
                print(records)
                if records:
                    request['session']['user_id'] = records[0]['id']
                res = await add_wordlist(request,data={"name":"新手起步"})
                if res:
                    wordlist_id = ujson.loads(res.body)['id']
                    r = await add_wordlists_word(request,wordlist_id,data={"word":"hello"})
                    return(r.body)
                if records:
                    return json(jsonify(records)[0])
    return json({},status = 400)

@youdao_bp.route('/wordlists/wechat/<wechat_token>', methods=['GET'])
async def get_wechat_word_h5(request,wechat_token):
    res = await add_user(request,wechat_token)
    wordlist_id = -1
    if res:
        await update_wechat_user(request,wechat_user=wechat_token)
        async with request.app.db.acquire() as cur:
            record = await cur.fetch("select * from word_list where user_id=%s"%request['session']['user_id'])
            if record:
                wordlist_id = record[0]['id']
    return redirect('http://bitnotice.susnote.com/html/WordLists.html')

@youdao_bp.route('/users/wechat_user',methods=['POST'])
async def update_wechat_user(request,user_id=None,wechat_user=None):
    data = {}
    try:
        data = ujson.loads(request.body)
    except:
        pass
    if not wechat_user:
        wechat_user = data.get('wechat_user')
    if not user_id:
        user_id = data.get('user_id') if data.get('user_id') else request['session'].get('user_id')

    if wechat_user and user_id:
        async with request.app.db as cur:
            sql = """update users set wechat_user=%s where id=%s returning *"""%(wechat_user,user_id)
            records = cur.fetch(sql)
            return json({})
    return json({},status=400)

@youdao_bp.route('/wordlists/<wordlist_id:int>/words', methods=['GET'])
async def get_wordlists_word(request,wordlist_id):
    user_id = None
    if request['session'].get('user_id'):
        user_id = request['session'].get('user_id')
    if user_id:
        async with request.app.db.acquire() as cur:
            records = await cur.fetch("select * from word_list where id=%s and user_id=%s"%(wordlist_id,user_id))
            if records:
                return json(jsonify(records)[0]["words"])
    return json({},status=400)

@youdao_bp.route('/wordlists/<wordlist_id:int>/words', methods=['POST'])
async def add_wordlists_word(request,wordlist_id,data={}):
    user_id = None
    try:
        if not data:
            data = ujson.loads(request.body)
    except:
        return json({},status=400)
    if request['session'].get('user_id'):
        user_id = request['session'].get('user_id')
    if user_id and data.get('word'):
        async with request.app.db as cur:
            records = await cur.fetch("select * from word_list where id=%s and user_id=%s"%(wordlist_id,user_id))
            if records:
                words = records[0]['words']
                if data.get('word') not in words:
                    words.append(data.get('word'))
                    words = str(list(words)).replace('[','{').replace(']','}').replace("'",'"')
                    records = await cur.fetch("""update word_list set words='%s' where id=%s returning *"""%(words,wordlist_id))
                    r = await cur.fetch("""insert into user_words (create_time,word,words_level,user_id,review_time, word_list_id) values (current_timestamp,'%s',%s,%s,current_timestamp,%s) returning *"""%(data.get('word'),0,user_id,wordlist_id))
                    print(r)
                    if records:
                        return json(jsonify(records)[0])
    return json({})

@youdao_bp.route('/wordlists', methods=['GET'])
async def get_wordlists(request):
    wordlist_id = request.args.get('id', 0)
    user_id = None
    if request['session'].get('user_id'):
        user_id = request['session'].get('user_id')
    if user_id and wordlist_id ==0:
        async with request.app.db.acquire() as cur:
            records = await cur.fetch("select * from word_list where user_id=%s"%(user_id))
            return json(jsonify(records))
    elif user_id:
        async with request.app.db.acquire() as cur:
            records = await cur.fetch("select * from word_list where user_id=%s and id =%s"%(user_id,wordlist_id))
            return json(jsonify(records))

    return json({},status=400)

@youdao_bp.route('/wordlists', methods=['DELETE'])
async def delete_wordlists(request,data={}):
    try:
        if not data:
            data = ujson.loads(request.body)
    except:
        return json({},status=400)
    wordlist_name = data.get("name").replace("'","''") if data.get("name") else "未命名"
    user_id = data.get("user_id") if data.get("user_id") else request['session'].get('user_id')
    if user_id:
        async with request.app.db as cur:
            r = await cur.fetch("select * from word_list where name='%s' and user_id=%s"%(wordlist_name,user_id))
            if r:
                wordlist_id = r[0]['id']
                await cur.fetch("delete from user_words where word_list_id=%s"%wordlist_id)
                res = await cur.fetch("delete from word_list where name='%s' and user_id=%s returning *"%(wordlist_name,user_id))
                return json(jsonify(r))
    return json({},status=400)

@youdao_bp.route('/wordlists', methods=['POST'])
async def add_wordlist(request,data={}):
    try:
        if not data:
            data = ujson.loads(request.body)
    except:
        return json({},status=400)
    wordlist_name = data.get("name").replace("'","''") if data.get("name") else "未命名"
    user_id = data.get("user_id") if data.get("user_id") else request['session'].get('user_id')
    if user_id:
        async with request.app.db as cur:
            r = await cur.fetch("select * from word_list where name='%s' and user_id=%s"%(wordlist_name,user_id))
            if r:
                return json(jsonify(r)[0])
            else:
                records = await cur.fetch("insert into word_list (create_time,words,name,category,user_id) VALUES (current_timestamp,'{}','%s','private',%s) returning *"%(wordlist_name,user_id))
            if records:
                return json(jsonify(records)[0])
    return json({},status=400)

@youdao_bp.route('/wordlists/<wordlist_id:int>', methods=['DELETE'])
async def delete_wordlist(request,wordlist_id):
    user_id = request['session'].get('user_id')
    if user_id:
        async with request.app.db as cur:
            records = await cur.fetch("delete from word_list where user_id=%s and id=%s returning *"%(user_id,wordlist_id))
            if records:
                return json(jsonify(records)[0])
    return json({},status=400)

@youdao_bp.route('/wordlists/<wordlist_id:int>/review/h5', methods=['GET'])
async def get_word_h5(request,wordlist_id):
    env = request.app.env
    template = await env.get_template('WordListReview.html').render_async(wordlist_id=wordlist_id)
    return html(template)

@youdao_bp.route('/wordlists/<wordlist_id:int>/h5', methods=['GET'])
async def get_word_h5(request,wordlist_id):
    env = request.app.env
    template = await env.get_template('WordList.html').render_async(wordlist_id=wordlist_id)
    return html(template)

async def parse_html(request,html,word):
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
        result['translation'] = await get_translation(request, word)

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

async def get_translation(request, word):
        """
        通过web版有道翻译抓取翻译结果
        :param word:str 关键字
        :return:list 翻译结果
        """
        cli = request.app.client.cli
        url = 'http://fanyi.youdao.com/translate?keyfrom=dict.top&i='+word

        async with cli.get(url) as res:
            if res.status == 200:
                data = await res.text()
                pattern = re.compile(r'"translateResult":\[(\[.+\])\]')
                m = pattern.search(data)
                result = ujson.loads(m.group(1))

        return [item['tgt'] for item in result]

@youdao_bp.route('/wechat/login', methods=['GET','POST'])
async def wechat_auth(request):
    if request.method == 'GET':
        token = 'WXokChinaCoinJJ'
        data = request.args
        signature = data.get('signature','')
        timestamp = data.get('timestamp','')
        nonce = data.get('nonce','')
        echostr = data.get('echostr','')
        s = [timestamp,nonce,token]
        s.sort()
        s = ''.join(s)
        s = s.encode('utf-8')
        if (hashlib.sha1(s).hexdigest() == signature):
            return html(echostr)
    else:
        rec = request.body
        xml_rec = ET.fromstring(rec)
        tou = xml_rec.find('ToUserName').text
        fromu = xml_rec.find('FromUserName').text
        content = xml_rec.find('Content').text
        if content in ["背单词","生词本"]:
            content = "<a href='http://bitnotice.susnote.com/words/wordlists/wechat/%s'>开始吧</a>"%fromu
        xml_rep = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>"

        response = html(xml_rep % (fromu,tou,str(int(time.time())), content))
        response.content_type = 'application/xml'
        return response

    return 'Hello weixin!'

@youdao_bp.route('/wordlists/<word_list_id:int>/review', methods=['GET'])
async def get_word_level(request,word_list_id):
    user_id = request['session'].get('user_id')
    words = []
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    async with request.app.db.acquire() as cur:
        records = await cur.fetch("""select word from user_words where word_list_id=%s and review_time< '%s'"""%(word_list_id,current_time))
        for record in jsonify(records):
            words.append(record['word'])
        return json(words)
    return json([])

@youdao_bp.route('/wordlists/<word_list_id:int>/review', methods=['PUT'])
async def update_word_level(request,word_list_id,words=None):
    user_id = request['session'].get('user_id')
    result = []
    if not words:
        words = ujson.loads(request.body)
    for word in words:
        word_text = word['word']
        async with request.app.db.acquire() as cur:
            record = await cur.fetch("""select words_level from user_words where word='%s' and user_id=%s and word_list_id=%s"""%(word_text,user_id,word_list_id))
            level = record[0]["words_level"]
        state = word['state']
        if state == 'remember':
            level = level+1 if level<=11 else level
            review_time = datetime.datetime.now() + review_time_list[str(level)]
            async with request.app.db.acquire() as cur:
                r = await cur.fetch("""update user_words set words_level = %s,review_time= '%s' where user_id=%s and word='%s' returning *"""%(level,review_time.strftime('%Y-%m-%d %H:%M:%S'),user_id,word_text))
        elif state == 'confuse':
            review_time = datetime.datetime.now()
            async with request.app.db.acquire() as cur:
                r = await cur.fetch("""update user_words set words_level = %s,review_time= '%s' where user_id=%s and word='%s' returning *"""%(level,review_time.strftime('%Y-%m-%d %H:%M:%S'),user_id,word_text))
        elif state == 'not remember':
            level = 0
            async with request.app.db.acquire() as cur:
                r = await cur.fetch("""update user_words set words_level = %s where user_id=%s and word='%s' returning *"""%(level,user_id,word_text))
        result.append(jsonify(r))
    return json(result)


