# -*- coding: utf-8 -*-


import os
import os.path
import string
import hashlib
import warnings

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import views, mixins, exceptions, parsers
from rest_framework.request import clone_request
from rest_framework.settings import api_settings
from rest_framework import status
from rest_framework.response import Response

import apps.genapi.views


class File(views.APIView):
    parser_classes = (parsers.FileUploadParser,)

    def post(self, request, *args, **kwargs):
        return self.upload(request, *args, **kwargs)

    def upload(self, request, *args, **kwargs):
        file_obj = request.FILES['file']
        file_countent =  file_obj.read()
        md5sum = hashlib.md5(file_countent).hexdigest()
        name, ext = os.path.splitext(file_obj.name)
        xname = int2base(string.atol(md5sum, 16), 64)
        dstname = "%s_banana_20141031_%s%s"%(xname, name, ext)
        path = default_storage.save(
            '%s/%s'%(dstname[0], dstname),
            ContentFile(file_countent)
        )
        return Response(
            {
                'dstname':   dstname,
                'md5sum':    md5sum,
                'srcname':   file_obj.name
            },
            status=status.HTTP_201_CREATED
        )


def int2base(x,b,alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789__'):
    'convert an integer to its string representation in a given base'
    if b<2 or b>len(alphabet):
        raise AssertionError("int2base base out of range")
    if type(x) == complex: # return a tuple
        return ( int2base(x.real,b,alphabet) , int2base(x.imag,b,alphabet) )
    if x<=0:
        if x==0:
            return alphabet[0]
        else:
            return  'm' + int2base(-x,b,alphabet)
    # else x is non-negative real
    rets=''
    while x>0:
        x,idx = divmod(x,b)
        rets = alphabet[idx] + rets
    return rets
