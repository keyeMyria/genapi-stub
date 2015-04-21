# -*- coding: utf-8 -*-

import six

import copy
import logging
from django.forms.models import model_to_dict

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from .mixins import Common

from django.db import IntegrityError


class Create(Common, generics.ListCreateAPIView):
    logger = logging.getLogger('apps.genapi.views.Create')

    errors = None

    def post(self, request, *args, **kwargs):
        xdata   = kwargs.get('xdata', request.DATA)

        if(isinstance(xdata, list)):
            return self.post_list(request, xdata, *args, **kwargs)

        results = xdata.get('results', None)
        count = xdata.get('count', None)
        if ((None != results) and (None != count) and (isinstance(results, list))):
            return self.post_list(request, results, *args, **kwargs)

        return self.create(request, *args, **kwargs)


    def post_list(self, request, xdata, *args, **kwargs):
        res_data = []
        status_code = None
        count = len(xdata)
        for index, data in enumerate(xdata):
            xrequest = copy.copy(request)
            xrequest._data = data
            res = self.create(xrequest, *args, **kwargs)
            status_code = res.status_code
            res.data['__status_code'] = status_code
            res_data.append(res.data)
        return  Response(
            {
                'results': res_data,
                'count' : count
            },
            status = status_code,
        )



    def get_xdata(self, request,  *args, **kwargs):
        partial = kwargs.pop('partial', False)
        xdata   = kwargs.pop('xdata', request.DATA)
        if(not xdata):
            raise self.http_method_empty_request()
        return (partial, xdata, kwargs)


    def get_or_create(self, request, *args, **kwargs):
        (partial, xdata, kwargs) = self.get_xdata(request, *args, **kwargs)
        baseno = self.get_baseno(request, *args, **kwargs)

        self.object = None
        if hasattr(self.model, 'baseno'):
            self.object = self.model(
                baseno = self.get_baseno(request, *args, **kwargs)
            )
        else:
            self.object = self.model()


        if(not xdata):
            return Response(
                {'detail2':'empty request'},
                status = status.HTTP_400_BAD_REQUEST
            )

        self.in_serializer = self.serializer_class(
            self.object,
            data    = xdata,
            files   = request.FILES,
            partial = partial
        )

        if(not self.in_serializer.is_valid()):
            return Response(
            self.in_serializer.errors,
            status = status.HTTP_400_BAD_REQUEST
        )

        self.xqueryset = self.model.objects.filter()

        if hasattr(self.model, 'baseno'):
            self.xqueryset = self.xqueryset.filter(
                baseno = baseno
            )

        self.in_serializer.data.pop("baseno", None)

        pk = self.in_serializer.data.get(self.model._meta.pk.attname, None)
        if(not pk):
            self.in_serializer.data.pop(self.model._meta.pk.attname, None)

        if(not self.in_serializer.object):
            obj = self.model()
            for key, val in six.iteritems(self.in_serializer.data):
                setattr(obj, key, val)
            self.in_serializer.object = obj


        truedata =  self.in_serializer.object.to_dict()
        self.logger.debug("xdata \n = %s"%((self.in_serializer.data,),))


        x = self.pre_save(self.in_serializer.object)



        if(x):
            self.in_serializer.object = x

        if(self.errors):
            return Response(
                self.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        truedata =  model_to_dict(self.in_serializer.object)

        self.logger.debug("truedata \n = %s"%truedata)

        pk = truedata.get(self.model._meta.pk.attname, None)
        if(not pk):
            truedata.pop(self.model._meta.pk.attname, None)


        fakedata = {}
        for key, val in six.iteritems(self.in_serializer.data):
            if not (key in self.model._meta.get_all_field_names()):
                fakedata[key] = val
            else:
                if(not self.in_serializer.object):
                    truedata[key] = val

        self.xobject, created = self.db_get_or_create(
            self.xqueryset,
            **truedata
        )

        for key, val in six.iteritems(fakedata):
            setattr(self.xobject, key, val)

        x = self.post_save(self.xobject, created)
        if(x):
            self.xobject = x

        ydata = {}
        for key, val in six.iteritems(self.in_serializer.data):
            ydata[key] = getattr(self.xobject, key)


        self.logger.debug("ydata \n = %s"%ydata)


        self.out_serializer = self.serializer_class(
            self.xobject,
            data    = ydata,
            files   = request.FILES,
            partial = partial
        )

        if(self.errors):
            return Response(
                self.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        if(not self.out_serializer.is_valid()):
            return Response(
                self.out_serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        self.logger.debug("self.out_serializer.data \n = %s"%self.out_serializer.data)

        if(created):
            return Response(self.out_serializer.data, status=status.HTTP_201_CREATED)
        return Response(self.out_serializer.data, status=status.HTTP_200_OK)


    def db_get_or_create(self, queryset, **kwargs):
        lookup = kwargs.copy()
        try:
            res = queryset.get_or_create(
                **lookup
            )
        except IntegrityError:
            self.logger.error("IntegrityError for %s"%(lookup,))
            res = queryset.get(**lookup)
        return res

    def create(self, request, *args, **kwargs):
        (partial, xdata, kwargs) = self.get_xdata(request, *args, **kwargs)

        if(not xdata):
            return Response(
                {'detail':'empty request'},
                status = status.HTTP_400_BAD_REQUEST
            )

        self.object = None
        if hasattr(self.model, 'baseno'):
            self.object = self.model(
                baseno = self.get_baseno(request, *args, **kwargs)
            )
        else:
            self.object = self.model()



        serializer = self.serializer_class(self.object,
            data    = xdata,
            files   = request.FILES,
            partial = partial
        )


        return self.serializer_create(serializer, *args, **kwargs)

    def serializer_create(self, serializer, *args, **kwargs):
        if serializer.is_valid():
            if(hasattr(self.object.__class__, 'next')):
                self.object.pk = self.object.__class__.next()
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            success_status_code = status.HTTP_201_CREATED
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status = success_status_code,
                headers = headers
            )
        return Response(
            serializer.errors,
            status = status.HTTP_400_BAD_REQUEST
        )


    def get_success_headers(self, data):
        try:
            return {'Location': data['url']}
        except (TypeError, KeyError):
            return {'Nolocation': 'Nolocation'}
