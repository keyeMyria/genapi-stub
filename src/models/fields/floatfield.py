# -*- coding: utf-8 -*-

from django.db import models

import decimal

from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class FloatField(models.DecimalField):

    def __init__(self,
                 verbose_name=None,
                 name=None,
                 max_digits=20,
                 decimal_places=10,
                 **kwargs
        ):
        self.max_digits, self.decimal_places = max_digits, decimal_places
        models.DecimalField.__init__(
            self,
            verbose_name,
            name,
            max_digits = max_digits,
            decimal_places = decimal_places,
            **kwargs
        )


    def formfield(self, **kwargs):
        defaults = {
            'max_digits': self.max_digits,
            'decimal_places':self.decimal_places
        }
        defaults.update(kwargs)
        return super(DecimalField, self).formfield(**defaults)


    def to_python(self, value):
        if(None == value) and self.null == False:
            return 0

        return float(decimal.Decimal(models.DecimalField.to_python(self, value)))
