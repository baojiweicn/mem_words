#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Create on 2017-04-25
@author: zhaoye
'''

import logging
from playhouse.migrate import *
from peewee import ProgrammingError

from config import DB_CONFIG
from common.migrations import MigrationModel
from models import *


db = PostgresqlDatabase(**DB_CONFIG)
migrator = PostgresqlMigrator(db)


class WordAudioMigration(MigrationModel):
    _model = WordAudio
    _db = db
    _migrator = migrator

    _migrator = migrator

class WordTranslateMigration(MigrationModel):
    _model = WordTranslate
    _db = db
    _migrator = migrator

    _migrator = migrator

def migrations():
    word_audio = WordAudioMigration()
    word_translate = WordTranslateMigration()

    try:
        with db.transaction():
            #rec.migrate_v1()
            print("Success Migration")
    except ProgrammingError as e:
        raise e
    except Exception as e:
        raise e

if __name__ == '__main__':
    migrations()
