# -*- coding: utf-8 -*-

from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MAX_POSITIVE_INT = 4294967295;

@DbFieldDecorator()
class PositiveIntegerField(models.PositiveIntegerField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 max_value = MAX_POSITIVE_INT,
                 **kwargs
        ):
        self.max_value = max_value
        models.PositiveIntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'max_value':self.max_value
        }
        defaults.update(kwargs)
        return super(PositiveIntegerField, self).formfield(**defaults)

