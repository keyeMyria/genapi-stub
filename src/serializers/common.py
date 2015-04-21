# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.compat import get_concrete_model, six
from rest_framework.relations import *
from rest_framework.fields import *

from apps.genapi.utils.log.logmeta import LogMeta
from apps.genapi.utils.log.logmeta import LogModelMeta


from django.utils.six import with_metaclass

TABLE_FORMATS = [
    'csv',
    'xlsx',
    'xls'
]

class Common(serializers.HyperlinkedModelSerializer):
    _id = serializers.Field(source="pk")

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(Common, self).__init__(*args, **kwargs)
        request = self.context.get('request')

        if(request):
            fields = request.QUERY_PARAMS.getlist('_fields')

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def get_fields(self, *args, **kwargs):
        self.opts.fields = list(self.opts.fields)
        format = self.context.get('format')

        if(format in TABLE_FORMATS):
            self.opts.fields = ['_id'] + self.opts.fields
        else:
            self.opts.fields = sorted(self.opts.fields)

        return super(Common, self).get_fields(*args, **kwargs)


    def full_clean(self, instance):
        try:
            instance.full_clean(exclude=self.get_validation_exclusions())
        except ValidationError as err:
            self._errors = err.message_dict
            return None
        return instance
