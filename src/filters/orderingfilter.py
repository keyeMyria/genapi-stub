from __future__ import unicode_literals
from django.db import models
from rest_framework.compat import django_filters, six, guardian
from functools import reduce
import operator

from django.db.models import Q

from .basefilterbackend import BaseFilterBackend

from apps.genapi.src.utils import tobool

FilterSet = django_filters and django_filters.FilterSet or None

class OrderingFilter(BaseFilterBackend):
    ordering_param = 'ordering'  # The URL query parameter used for the ordering.
    ordering_fields = None

    def get_ordering(self, request):
        """
        Ordering is set by a comma delimited ?ordering=... query parameter.
        """
        params = request.QUERY_PARAMS.get(self.ordering_param)
        if params:
            return [param.strip() for param in params.split(',')]

    def get_default_ordering(self, view):
        ordering = getattr(view, 'ordering', None)
        if isinstance(ordering, six.string_types):
            return (ordering,)
        return ordering

    def remove_invalid_fields(self, queryset, ordering, view):
        valid_fields = getattr(view, 'ordering_fields', self.ordering_fields)

        if valid_fields is None:
            # Default to allowing filtering on serializer fields
            serializer_class = getattr(view, 'serializer_class')
            if serializer_class is None:
                msg = ("Cannot use %s on a view which does not have either a "
                       "'serializer_class' or 'ordering_fields' attribute.")
                raise ImproperlyConfigured(msg % self.__class__.__name__)
            valid_fields = [
                field.source or field_name
                for field_name, field in serializer_class().fields.items()
                if not getattr(field, 'write_only', False)
            ]
        elif valid_fields == '__all__':
            # View explictly allows filtering on any model field
            valid_fields = [field.name for field in queryset.model._meta.fields]
            valid_fields += queryset.query.aggregates.keys()

        return [term for term in ordering if term.lstrip('-') in valid_fields]

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request)


        if ordering:
            # Skip any incorrect parameters
            ordering = self.remove_invalid_fields(queryset, ordering, view)



        if not ordering:
            # Use 'ordering' attribute by default
            ordering = self.get_default_ordering(view)

        if ordering:
            qs = queryset.order_by(*ordering)

            print "\n\n\n\n\nqs.str_sql = ", ordering, qs.str_sql()


            return qs



        return queryset
