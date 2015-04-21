
from django.db import models

from .dbfielddecorator      import DbFieldDecorator

MIN_MEDIUM_INT = -8388608; 
MAX_MEDIUM_INT = 8388607; 

@DbFieldDecorator()
class MediumIntegerField(models.IntegerField):
    #description = _("Medium integer")
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 min_value = MIN_MEDIUM_INT,
                 max_value = MAX_MEDIUM_INT,
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
        return super(MediumIntegerField, self).formfield(**defaults)
    
    def get_internal_type(self):
        return "MediumIntegerField"
