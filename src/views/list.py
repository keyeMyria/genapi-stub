# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.response import Response

from .mixins import Common

from django.conf import settings
from django.http import HttpResponseRedirect
import urllib

import random



class List(Common, generics.ListCreateAPIView):

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(self.object_list)
        page = self.transform_page(page)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)
            
        return Response(serializer.data)
