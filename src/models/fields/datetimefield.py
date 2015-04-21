 # -*- coding: utf-8 -*-

from django.db import models

from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class DateTimeField(models.DateTimeField):

    def to_python(self, value):
        if(0 == value):
            return 0

        return models.DateTimeField.to_python(self, value)


    def get_db_prep_value(self, value, connection, prepared=False):
        if(None == value):
            return 0
        if(0 == value):
            return 0
        if('0000-00-00 00:00:00' == value):
            return 0
        if('0' == value):
            return 0
        return models.DateTimeField.get_db_prep_value(
            self,
            value,
            connection,
            prepared
        )


    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)

        if(val == '0000-00-00 00:00:00'):
            return ''
        if(val == 0):
            return ''

        return models.DateTimeField.value_to_string(self, obj)
