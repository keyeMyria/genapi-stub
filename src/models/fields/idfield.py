# -*- coding: utf-8 -*-

from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MAX_INT = 2147483647

@DbFieldDecorator()
class IdField(models.IntegerField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 min_value = - MAX_INT - 1,
                 max_value = MAX_INT,
                 **kwargs
        ):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'min_value': self.min_value,
            'max_value':self.max_value
        }
        defaults.update(kwargs)
        return super(IntegerField, self).formfield(**defaults)

