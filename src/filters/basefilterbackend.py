"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals
from django.db import models
from rest_framework.compat import django_filters, six, guardian
from functools import reduce
import operator

from django.utils.six import with_metaclass

FilterSet = django_filters and django_filters.FilterSet or None


from apps.genapi.utils.log.logmeta import LogMeta

class BaseFilterBackend(with_metaclass(LogMeta)):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        return queryset


