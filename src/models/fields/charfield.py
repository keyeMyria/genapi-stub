 # -*- coding: utf-8 -*-

from django.db import models


from .dbfielddecorator      import DbFieldDecorator

@DbFieldDecorator()
class CharField(models.CharField):
    pass
