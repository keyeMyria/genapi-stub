# -*- coding: utf-8 -*-

from rest_framework import generics


from rest_framework import status
from rest_framework.response import Response


from .mixins import Common

import re

import logging

class Destroy(Common,generics.RetrieveUpdateDestroyAPIView):

    def delete(self, request, *args, **kwargs):
        self.handle_queryset(request, *args, **kwargs)
        return self.destroy(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()
        self.queryset = self.filter_object(request, *args, **kwargs)

        if(self.queryset != None):
            #logger = logging.getLogger('django.db.backends')
            #str_sql = self.queryset.str_sql()
            #str_sql = str_sql.replace('"', '')
            #str_sql = re.sub("SELECT .* FROM", "delete from", str_sql)
            #logger.warn(str_sql)
            #list(self.queryset.model.objects.raw(str_sql))
            self.queryset._raw_delete(self.queryset.db)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)



    def filter_object(self, request, pk=None, *args, **kwargs):
        self.queryset = self.queryset.filter(pk = pk)
        return self.queryset
