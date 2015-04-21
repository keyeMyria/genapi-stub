
from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MIN_SMALL_INT = -32768;
MAX_SMALL_INT = 32767; 

@DbFieldDecorator()
class SmallIntegerField(models.SmallIntegerField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 min_value = MIN_SMALL_INT,
                 max_value = MAX_SMALL_INT,
                 **kwargs
        ):
        self.min_value, self.max_value = min_value, max_value
        models.SmallIntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'min_value':self.min_value,
            'max_value':self.max_value,
        }
        defaults.update(kwargs)
        return super(SmallIntegerField, self).formfield(**defaults)
