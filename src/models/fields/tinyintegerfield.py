
from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MIN_TINY_INT = -128; 
MAX_TINY_INT = 127;

@DbFieldDecorator()
class TinyIntegerField(models.IntegerField):
    #description = _("Tiny integer")
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 min_value = MIN_TINY_INT,
                 max_value = MAX_TINY_INT,
                 **kwargs
        ):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)


    def formfield(self, **kwargs):
        defaults = {
            'min_value':self.min_value,
            'max_value':self.max_value,
        }
        defaults.update(kwargs)
        return super(TinyIntegerField, self).formfield(**defaults)
    
    def get_internal_type(self):
        return "TinyIntegerField"
