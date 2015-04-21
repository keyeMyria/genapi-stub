 # -*- coding: utf-8 -*-

import uuid

from hashlib import md5

from django.db import models

from django.conf import settings

from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class PositiveBigIntegerField(models.BigIntegerField):

    @classmethod
    def uniq(cls):
        return int(md5(str(uuid.uuid4())).hexdigest()[0:8], 16)

    def db_type(self, *args, **kwargs):
        return "bigint unsigned"


    def formfield(self, **kwargs):
        defaults = {'min_value': 0,
                    'max_value': models.BigIntegerField.MAX_BIGINT * 2 - 1}
        defaults.update(kwargs)
        return super(PositiveBigIntegerField, self).formfield(**defaults)
