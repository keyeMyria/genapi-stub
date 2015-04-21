from importlib import import_module
import time
import uuid
import json
import xml.dom.minidom
import logging

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date

from django.utils.http import *

from apps.genapi.utils import base_encode


class LogMiddleware(object):

    def __init__(self):
        self.request_logger = logging.getLogger('apps.genapi.request')
        self.client_logger  = logging.getLogger('apps.genapi.client')
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def process_request(self, request):
        if ("/logaction" in request.path) or ("/logdebug" in request.path) :
            self.process_request_log(request, self.client_logger)
        else:
            self.process_request_log(request, self.request_logger)

    def process_response(self, request, response):
        if ("/logaction" in request.path) or ("/logdebug" in request.path) :
            self.process_response_log(request, response, self.client_logger)
        else:
            self.process_response_log(request, response, self.request_logger)
        return response

    def process_request_log(self, request, logger = None):
        request = self.handle_request(request)
        if not logger:
            logger = self.request_logger;
        headers = ""
        for i in request.META:
            if "HTTP_" in i:
                name = i.replace("HTTP_", "")
                name = "-".join([x.capitalize() for x in name.split("_")])
                headers += '\n%s: %s' %(name, request.META[i])
        body = self.pp_data(request.body)
        get_params = ""
        for param in request.GET:
            get_params +=   "\n    %s: %s"%(param, request.GET[param])

        file_params = ""
        for param in request.FILES:
            fileobj = request.FILES[param]
            file_params +=  "\n    %s: %s <<{" \
                            "\n        charset: %s; " \
                            "\n        content-type: %s;" \
                            "\n        size: %s b" \
                            "\n    }>>"%(
                param,
                fileobj,
                fileobj.charset,
                fileobj.content_type,
                fileobj._size
            )
        logger.info(
        u"\n"
            "\n================< REQ %s %s >================\n"
            "\n%s %s %s 1.X"
            "%s"
            "\nContent-Length: %s"
            "\nContent-Type: %s"
            "\nGet-Params: <<{%s\n}>>"
            "\nFile-Params: <<{%s\n}>>"
            "\n"
            "\n%s\n"
            "\n================</REQ %s %s >================\n"
            "\n"%(
                request.user_uuid,
                request.uuid,
                request.method,
                request.get_full_path(),
                request.protocol,
                headers,
                request.META.get('CONTENT_LENGTH', None),
                request.META.get('CONTENT_TYPE', None),
                get_params,
                file_params,
                body,
                request.user_uuid,
                request.uuid,
            )
        )

    def handle_request(self, request):
        request = self.handle_user_uuid(request)
        request = self.handle_uuid(request)
        request = self.handle_protocol(request)
        return request

    def handle_user_uuid(self, request):
        if(hasattr(request, 'user_uuid')):
            return request
        request.user_uuid = None
        if(hasattr(request, 'session')):
            __user_uuid = request.session.get(
                'user_uuid',
                request.META.get('HTTP_X_USER_UUID', base_encode(uuid.uuid4().int))
            )
            if(not __user_uuid):
                __user_uuid = base_encode(uuid.uuid4().int)
            request.user_uuid = __user_uuid
            request.session['user_uuid'] = "%s"%(request.user_uuid)
        return request;

    def handle_uuid(self, request):
        if(hasattr(request, 'uuid')):
            return request
        request.uuid = base_encode(uuid.uuid4().int)
        return request

    def handle_protocol(self, request):
        request.protocol = None
        if(hasattr(request, 'protocol')):
            return request
        request.protocol = request.build_absolute_uri().split(':')[0].upper()
        return request

    def process_response_log(self, request, response, logger = None):
        if not logger:
            logger = self.request_logger;
        request = self.handle_request(request)
        headers = ""
        for header in response._headers:
            headers += "\n%s: %s"%response._headers[header]
        if(response.status_code != 500):
            content = len(response.content)
            logger.info(
            u"\n"
                "\n================< RES %s %s >================\n"
                "\n%s %s 1.X %s %s %s\n"
                "\n%s\n"
                "\n================</RES %s %s >================\n"
                "\n"%(
                    request.user_uuid,
                    request.uuid,
                    request.protocol,
                    request.method,
                    str(response.status_code),
                    response.reason_phrase,
                    headers,
                    content,
                    request.user_uuid,
                    request.uuid,
                )
            )
        else:
            logger.info(
            u"\n"
                "\n================< RES %s %s >================\n"
                "\n%s 1.X %s %s %s\n"
                "\n================</RES %s %s >================\n"
                "\n"%(
                    request.user_uuid, request.uuid,
                    request.protocol,
                    str(response.status_code),
                    response.reason_phrase,
                    headers,
                    request.user_uuid, request.uuid,
                )
            )
        response['X-Request-Uuid'] = request.uuid
        response['X-User-Uuid'] = request.user_uuid
        return response

    def pp_data(self, data):
        res = '<<"binary data ...">>'
        try:
            res = unicode(
                json.dumps(
                    json.loads(data),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False
                ).encode('utf8'),
                'utf8'
            )
        except:
            try:
                xmlc = xml.dom.minidom.parseString(data)
                res = xmlc.toprettyxml(indent="  ")
            except:
                try:
                    res = unicode(data, 'utf8')
                except:
                    pass
        return res;
