
from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MAX_POSITIVE_SMALL_INT = 65535;

@DbFieldDecorator()
class PositiveSmallIntegerField(models.PositiveSmallIntegerField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 max_value = MAX_POSITIVE_SMALL_INT,
                 **kwargs
        ):
        self.max_value = max_value
        models.PositiveSmallIntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'max_value':self.max_value
        }
        defaults.update(kwargs)
        return super(PositiveSmallIntegerField, self).formfield(**defaults)
