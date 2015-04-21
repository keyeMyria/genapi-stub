# -*- coding: utf-8 -*-

import inspect

from django.utils.six import with_metaclass

from apps.genapi.utils.log.logmeta import LogMeta

from rest_framework.views import APIView

from rest_framework import status, exceptions

from django.utils.translation import ugettext_lazy as _

from django.db.models import Q
import operator

from apps.genapi.utils import toint
import logging
from django.http import Http404

from apps.genapi.models import Sharded



class EmptyRequest(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'empty request'

class Common(APIView, with_metaclass(LogMeta)):

    logger = logging.getLogger('apps.genapi.views.Common')



    transform_backends = []

    def http_method_not_found(self, *args, **kwargs):
        """
        If `request.method` does not correspond to a handler method,
        determine what kind of exception to raise.
        """
        raise Http404

    def http_method_empty_request(self, *args, **kwargs):
        """
        If `request.method` does not correspond to a handler method,
        determine what kind of exception to raise.
        """
        raise EmptyRequest


    @property
    def serializer(self, *args, **kwargs):
        return self.__class__.serializer_class(*args, **kwargs)


    def handle_queryset(self, request, *args, **kwargs):
        self.queryset = self.queryset_init(request, *args, **kwargs)
        self.queryset = self.queryset_handle_baseno(request, *args, **kwargs)
        return self.queryset

    def queryset_init(self, request, *args, **kwargs):
        self.queryset = self.model._default_manager.all()
        return self.queryset;


    def is_sharded_baseno(self):
        return (
            issubclass(self.model, Sharded)
            and hasattr(self.model, 'baseno')
        )


    def queryset_handle_baseno(self, request, *args, **kwargs):
        '''
        Берет параметр `номера шарда` из параметров HTTP запроса (baseno).
        И добавляет его к параметрам запроса к БД.
        '''
        pkstr = self.kwargs.get(self.pk_url_kwarg, None)
        if(not pkstr or not hasattr(pkstr, 'split')):
            return self.queryset_handle_baseno_plain(request, *args, **kwargs)

        if(self.is_sharded_baseno()):
            pklist = pkstr.split("-")
            if(len(pklist) > 1):
                baseno = toint(pklist[0], None)
                if not baseno:
                    raise Http404
                self.kwargs["baseno"] = baseno;
                self.kwargs[self.pk_url_kwarg] = pklist[1]
                return self.queryset_apply_baseno(baseno)
        return self.queryset_handle_baseno_plain(request, *args, **kwargs)


    def queryset_handle_baseno_plain(self, request, *args, **kwargs):
        '''
        Берет параметр `номера шарда` из параметров HTTP запроса (baseno).
        И добавляет его к параметрам запроса к БД.
        '''
        baseno = self.get_baseno(request, *args, **kwargs)
        return self.queryset_apply_baseno(baseno)

    def queryset_apply_baseno(self, baseno):
        if(self.is_sharded_baseno()):
            baseno = toint(baseno, None)
            if baseno :
                self.kwargs['baseno'] = baseno
                self.queryset = self.queryset.filter(baseno = baseno)
            else:
                raise Http404
        return self.queryset



    def get_baseno(self, request, *args, **kwargs):
        qbaseno = self.get_qbaseno(request, *args, **kwargs)
        if qbaseno:
            return qbaseno
        dbaseno = self.get_dbaseno(request, *args, **kwargs)
        if dbaseno:
            return dbaseno
        return None

    def get_qbaseno(self, request, *args, **kwargs):
        baseno = request.QUERY_PARAMS.get('baseno', None)
        baseno = toint(baseno, None)
        return baseno

    def get_dbaseno(self, request, *args, **kwargs):
        if request.DATA:
            return request.DATA.get('baseno', None)
        return None

    def get_transform_backends(self):
        transform_backends = self.transform_backends or []
        return transform_backends

    def transform_page(self, page):
        page.object_list = self.transform_queryset(
            # A little hack with evaluating models
            [e for e in page.object_list]
        )
        return page

    def transform_queryset(self, queryset):
        for backend in self.get_transform_backends():
            queryset = backend().transform_page(self.request, queryset, self)
        return queryset

    def get_queryset(self):
        query_params = self.request.QUERY_PARAMS
        self.queryset = self.filter(query_params)
        return self.queryset

    def filter(self, query_params):
        fileterd = self.field_names_filter(query_params)
        self.queryset = self.get_queryset_by_filter(fileterd)
        return self.queryset

    def field_names_filter(self, query_params):
        model_field_names = self.model._meta.get_all_field_names()

        fileterd = {
            "%s__in"%(k): query_params.getlist(k)
            for k in set(model_field_names) & set(query_params.keys())
        }

        if(self.is_sharded_baseno()):
            fileterd['baseno'] = query_params.get('baseno')

        return fileterd

    def get_queryset_by_filter(self, fileterd):
        if(None == self.queryset):
            self.queryset = self.model.objects.all()
        baseno = fileterd.pop('baseno',None)
        if(baseno):
            if(not self.kwargs.get('baseno')):
                self.queryset = self.queryset.filter(baseno=baseno)
        self.queryset = self.queryset.filter(**dict(fileterd))
        return self.queryset



    def partial_func(
        self,
        request,
        view = None,
        view_class = None,
        action = None,
        *args,
        **kwargs
    ):
        if(view_class):
            view  = view_class()
        else:
            if(not view):
                view = self

        view.request    = request
        view.args       = args
        view.kwargs     = kwargs
        func = getattr(view, action)
        return func(request, *args, **kwargs)


    def partial_update(self, request, view = None, view_class = None, *args, **kwargs):

        return self.partial_func(
            request = request,
            view = view,
            view_class = view_class,
            action = 'update',
            *args,
            **kwargs
        )

        #if(view_class):
            #view  = view_class()

        #view.request    = request
        #view.args       = args
        #view.kwargs     = kwargs
        #return view.update(request, *args, **kwargs)

    def partial_create(self, request, view = None, view_class = None, *args, **kwargs):

        return self.partial_func(
            request = request,
            view = view,
            view_class = view_class,
            action = 'create',
            *args,
            **kwargs
        )

        #if(view_class):
            #view  = view_class()

        #view.request    = request
        #view.args       = args
        #view.kwargs     = kwargs
        #return view.create(request, *args, **kwargs)
