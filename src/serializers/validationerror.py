# -*- coding: utf-8 -*-

from rest_framework import serializers

class ValidationError(serializers.ValidationError):
    pass

