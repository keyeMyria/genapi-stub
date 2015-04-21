
from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MAX_POSITIVE_TINY_INT = 255; 

@DbFieldDecorator()
class PositiveTinyIntegerField(models.PositiveIntegerField):
    #description = _("Positive tiny integer")
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 max_value = MAX_POSITIVE_TINY_INT,
                 **kwargs
        ):
        self.max_value = max_value
        models.PositiveIntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'max_value':self.max_value,
        }
        defaults.update(kwargs)
        return super(PositiveTinyIntegerField, self).formfield(**defaults)
    
    def get_internal_type(self):
        return "PositiveTinyIntegerField"
