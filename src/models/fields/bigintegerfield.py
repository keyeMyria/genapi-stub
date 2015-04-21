 # -*- coding: utf-8 -*-

import uuid

from hashlib import md5

from django.db import models

from django.conf import settings

from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class BigIntegerField(models.BigIntegerField):

    @classmethod
    def uniq(cls):
        return int(md5(str(uuid.uuid4())).hexdigest()[0:8], 16)

    def db_type(self, *args, **kwargs):
        connection = kwargs.get('connection', None)
        if(connection):
            if (connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3'):
                return "bigint"

        return models.BigIntegerField.db_type(self, *args, **kwargs)
