# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied, FieldError
from django.http import Http404

from django.db import ProgrammingError

from django.utils.datastructures import SortedDict
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, exceptions
from rest_framework.compat import smart_text, HttpResponseBase, View
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils import formatting

from apps.genapi.models import WrongBaseno

import sys, traceback

import logging

def ehandler(exc):

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['X-Throttle-Wait-Seconds'] = '%d' % exc.wait

        return Response({'detail': exc.detail},
                        status=exc.status_code,
                        headers=headers)


    elif isinstance(exc, WrongBaseno):
        return Response({'detail': exc.detail},
                        status = status.HTTP_400_BAD_REQUEST,)

    elif isinstance(exc, Http404):
        errtype = str(sys.exc_info()[1])
        if("XXX Page is not 'last', nor can it be converted to an int." == errtype):
            return Response({
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'results': []
                },
                status=status.HTTP_200_OK
            )
        return Response({'detail': 'Not found'},
                        status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, PermissionDenied):
        return Response({'detail': 'Permission denied'},
                        status=status.HTTP_403_FORBIDDEN)

    elif isinstance(exc, ProgrammingError):
        return Response({'detail': 'Not found'},
                        status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, FieldError):
        return Response(response_exception_detail(exc),
                        status=status.HTTP_400_BAD_REQUEST)

    else:
        pass

    logging.error(format_exception(exc))

    return Response(
        response_exception(exc),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def response_exception(e):

    stack = traceback.extract_stack()
    stack = stack[:-2]

    stack_list = []
    indx = 0
    for file, line, fun, inst in stack:
        indx += 1
        stack_list.append({
            "indx": indx,
            "file": file,
            "line": line,
            "func": fun,
            "inst": inst

        })

    tb = traceback.extract_tb(sys.exc_info()[2])
    tb_list = []
    indx = 0
    for file, line, fun, inst in tb:
        indx += 1
        tb_list.append({
            "indx": indx,
            "file": file,
            "line": line,
            "func": fun,
            "inst": inst

        })

    return {
        'traceback': tb_list,
        'stack':stack_list,
        'detail': "".join(traceback.format_exception_only(
            sys.exc_info()[0],
            sys.exc_info()[1]
        )).replace('\n', '')
    }

def response_exception_detail(e):
    return {
        'detail': "".join(traceback.format_exception_only(
            sys.exc_info()[0],
            sys.exc_info()[1]
        )).replace('\n', '')
    }

def format_exception(e):
    exception_list = []
    exception_list = traceback.format_stack()
    exception_list = exception_list[:-2]
    exception_list.extend(traceback.format_tb(sys.exc_info()[2]))
    exception_list.extend(traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1]))

    exception_str = "Traceback (most recent call last):\n"
    exception_str += "".join(exception_list)
    # Removing the last \n
    exception_str = exception_str[:-1]

    return exception_str


