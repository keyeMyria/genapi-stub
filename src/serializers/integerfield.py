# -*- coding: utf-8 -*-

from rest_framework import serializers

MAX_INT = 2147483647


class IntegerField(serializers.IntegerField):

    def __init__(self, max_value=MAX_INT, min_value=-MAX_INT-1, *args, **kwargs):
        super(IntegerField, self).__init__(max_value,min_value,*args, **kwargs)
