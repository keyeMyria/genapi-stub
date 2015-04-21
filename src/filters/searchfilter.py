"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals
from django.db import models
from rest_framework.compat import django_filters, six, guardian
from functools import reduce
import operator

from django.db.models import Q

from .basefilterbackend import BaseFilterBackend

from apps.genapi.src.utils import tobool

FilterSet = django_filters and django_filters.FilterSet or None


class SearchFilter(BaseFilterBackend):
    search_param = 'search'  # The URL query parameter used for the search.

    def filter_queryset(self, request, qson, view):
        return  self.__class__.filter_qs(request, qson, view)


    @classmethod
    def filter_qs(cls, request, aqueryset, view, useor=False):
        search_fields = getattr(view, 'search_fields', None)

        if not search_fields:
            return aqueryset

        orm_lookups = [cls.construct_search(str(search_field))
                       for search_field in search_fields]

        querysets = []
        for search_term in cls.get_search_terms(request):
            or_queries = [
                Q(**{orm_lookup[0]: search_term})
                    for orm_lookup in orm_lookups
                        if (1 == orm_lookup[1] and search_term.isdigit())
                            or 0 == orm_lookup[1]
            ]
            querysets.append(aqueryset.filter(reduce(operator.or_, or_queries)))

        if(not querysets):
            return aqueryset

        if(useor):
            queryset = reduce(operator.or_,querysets)
        else:
            queryset = reduce(operator.and_,querysets)
        return queryset


    @classmethod
    def prm(cls, val):
        return tobool(val)


    @classmethod
    def get_search_terms(cls, request):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """

        params = request.QUERY_PARAMS.get(cls.search_param, '')
        return params   .replace(',', ' ')  \
                        .replace('*', ' ')  \
                        .replace('?', ' ')  \
                        .replace('[', ' ')  \
                        .replace(']', ' ')  \
                        .replace('(', ' ')  \
                        .replace(')', ' ')  \
                        .replace('\\', ' ') \
                        .split()

    @classmethod
    def fqs(
            cls,
            search_fields,
            search_terms,
            aqueryset,
            useor = False
        ):
            if not search_fields:
                return aqueryset
            if not search_terms:
                return aqueryset
            orm_lookups = [cls.construct_search(str(search_field))
                        for search_field in search_fields]

            querysets = []
            for search_term in search_terms:
                or_queries = [
                    Q(**{orm_lookup[0]: search_term})
                        for orm_lookup in orm_lookups
                            if (1 == orm_lookup[1] and search_term.isdigit())
                                or 0 == orm_lookup[1]
                ]
                #queryset = queryset.filter(reduce(operator.or_, or_queries))
                querysets.append(aqueryset.filter(reduce(operator.or_, or_queries)))

            if(not querysets):
                return aqueryset

            if(useor):
                queryset = reduce(operator.or_,querysets)
            else:
                queryset = reduce(operator.and_,querysets)
            return queryset


    @classmethod
    def construct_search(cls, field_name):
        #    295655767
        if field_name.startswith('^'):
            return ("%s__istartswith" % field_name[1:], 0)
        elif field_name.startswith('='):
            return ("%s__iexact" % field_name[1:], 0)
        elif field_name.startswith('+'):
            return ("%s__exact" % field_name[1:], 1)
        elif field_name.startswith('@'):
            return ("%s__search" % field_name[1:], 0)
        else:
            return ("%s__icontains" % field_name, 0)
