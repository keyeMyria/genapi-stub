# -*- coding: utf-8 -*-

from rest_framework import serializers
from collections import Iterable


class Field(serializers.Field):
    pass


class WritableField(serializers.WritableField):
    pass


class SetField(serializers.WritableField):

    def to_native(self, obj):
        return list(obj)

    def from_native(self, data):
        if isinstance(data, Iterable):
            return set(data)
        return set([data])

