# -*- coding: utf-8 -*-

# from apps.pybsadm.models import OrderInfo
# x = OrderInfo.objects.get(orderid = 3314416)
# x.options = set(['deleted'])
# x.save()

from django.db import models

from django.utils.six import with_metaclass

from .charfield             import CharField

from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class SetField(with_metaclass(models.SubfieldBase, models.CharField)):

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            return 'varchar(100)'
        self.choices.append(('', ''))
        return "set({0})".format( ','.join("'%s'" % v[0] for v in self.choices))

    def to_python(self, value):
        if not value:
            return set()
        elif isinstance(value, set):
            return value
        elif isinstance(value, list):
            return set(value)
        elif isinstance(value, str):
            _list = value.split(",")
            return set(_list)
        elif isinstance(value, unicode):
            _list = value.split(",")
            return set(_list)

        return set()


    def get_prep_value(self, value):
        if(value == None):
            return ""
        return ",".join(["%s" % v for v in value])
