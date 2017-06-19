#!/usr/bin/env python
# encoding: utf-8

import datetime
from peewee import *
from playhouse.postgres_ext import *
from sanic_openapi import doc

class BaseModel(Model):
    id = PrimaryKeyField()
    create_time = DateTimeField(verbose_name='创建时间', default=datetime.datetime.now)

class WordAudio(BaseModel):
    word = CharField(max_length=128)
    audio_path = CharField(max_length=128)

    class Meta:
        db_table = 'word_audio'

class WordTranslate(BaseModel):
    word = CharField(max_length=128)
    translate = TextField(verbose_name='translate')

    class Meta:
        db_table = 'word_translate'
