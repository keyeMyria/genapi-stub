# -*- coding: utf-8 -*-
import six

from rest_framework import generics


from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import clone_request
from rest_framework.settings import api_settings
import warnings

from django.forms.models import model_to_dict

from .mixins import Common


import logging

#class __Detail(Common,generics.RetrieveUpdateDestroyAPIView):
    #pass

class Detail(Common,generics.RetrieveUpdateDestroyAPIView):

    errors = []

    def get(self, request, *args, **kwargs):
        self.queryset = self.handle_queryset(request, *args, **kwargs)

        x = self.retrieve(request, *args, **kwargs)
        return x

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        response_iter = iter(self.transform_queryset([self.object]))
        self.object = next(response_iter, None)
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


    def transform_queryset(self, queryset):
        for backend in self.get_transform_backends():
            queryset = backend().transform_page(self.request, queryset, self)
        return queryset


    def put(self, request, *args, **kwargs):
        self.handle_queryset(request, *args, **kwargs)
        return self.update(request, *args, **kwargs)


    def patch(self, request, *args, **kwargs):
        self.handle_queryset(request, *args, **kwargs)
        return self.update(request, partial = True, *args, **kwargs)

    def get_xdata(self, request,  *args, **kwargs):
        partial = kwargs.pop('partial', False)
        xdata   = kwargs.pop('xdata', request.DATA)
        if(not xdata):
            raise self.http_method_empty_request()
        return (partial, xdata, kwargs)


    def update(self, request, *args, **kwargs):
        (partial, xdata, kwargs) = self.get_xdata(request, *args, **kwargs)
        self.object = self.get_object()


        serializer = self.serializer_class(self.object,
            data    = xdata,
            files   = request.FILES,
            partial = True,
            allow_add_remove = False,
            many    = False,
        )

        return self.serializer_update(serializer, *args, **kwargs)

    def serializer_update(self, serializer, *args, **kwargs):

        ## Пока оставим этот костыль
        ## Но по-хорошему, должно передаваться извне
        serializer.partial = True

        update_fields = []
        if(serializer.partial):
            for key, val in six.iteritems(serializer.init_data):
                if (key in self.model._meta.get_all_field_names()
                    #and key in serializer.data.keys()
                    and key != self.model._meta.pk.attname
                    ):
                    update_fields.append(key)


        if self.object is None:
            return Response(
                {"detail": "Not found"},
                status = status.HTTP_404_NOT_FOUND
            )
        else:
            created = False
            save_kwargs = {'force_update': True, "update_fields": update_fields}
            success_status_code = status.HTTP_200_OK

        logging.debug("save_kwargs = %s"%save_kwargs)

        logging.debug("serializer.object = %s"%serializer.object)

        if serializer.is_valid():
            try:
                self.pre_save(serializer.object)
                if(self.errors):
                    return Response(
                        self.errors,
                        status = status.HTTP_400_BAD_REQUEST
                    )
            except ValidationError as err:
                # full_clean on model instance may be called in pre_save, so we
                # have to handle eventual errors.
                return Response(err.message_dict, status=status.HTTP_400_BAD_REQUEST)

            self.object = self.db_save(serializer, **save_kwargs)
            if(self.errors):
                return Response(
                    self.errors,
                    status = status.HTTP_400_BAD_REQUEST
                )

            self.post_save(self.object, created=created)
            return Response(serializer.data, status=success_status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    #def db_save(self, serializer, **save_kwargs):
        #return serializer.save(**save_kwargs)


    def db_save(self, serializer, **save_kwargs):

        if(self.object.to_dict() != self.object.initial_copy.to_dict()):
            return serializer.save(**save_kwargs)
        else:
            pass
        return self.object.initial_copy

