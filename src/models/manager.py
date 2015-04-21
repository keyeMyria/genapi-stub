# -*- coding: utf-8 -*-

import django.db.models


import apps.genapi.caching.base

from .queryset import QuerySet

from caching.base import CachingManager

#class Manager(CachingManager):

class Manager(django.db.models.Manager):
    def __init__(self, caching_timeout = None,  *arg, **kvargs):
        super(Manager, self).__init__(*arg, **kvargs)
        self.caching_timeout = caching_timeout

    def get_query_set(self):
        qs = QuerySet(self.model)
        if(None != self.caching_timeout):
            qs.timeout = self.caching_timeout
        return qs

    def get_queryset(self):
        qs = QuerySet(self.model)
        if(None != self.caching_timeout):
            qs.timeout = self.caching_timeout
        return qs

    def insert(self, *args, **kwargs):
        return self.all().insert(*args, **kwargs)

    def replace(self, *args, **kwargs):
        return self.all().replace(*args, **kwargs)

    def insert_update(self, *args, **kwargs):
        return self.all().insert_update(*args, **kwargs)

    def insert_ignore(self, *args, **kwargs):
        return self.all().insert_ignore(*args, **kwargs)


