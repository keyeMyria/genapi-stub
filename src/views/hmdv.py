# -*- coding: utf-8 -*-

import inspect

from django.views.generic.base import View

from .mixins import Common

from django.template import TemplateDoesNotExist

class Hmdv(Common):
    '''
    Http Method Depended View
    '''
    routes = {
    }
    name = None



    def dispatch(self, request, *args, **kwargs):

        self.headers = {}
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.args = args
        self.kwargs = kwargs

        response = None

        try:
            self.initial(request, *args, **kwargs)
            response = self._dispatch_response(request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


    def _dispatch_response(self, request, *args, **kwargs):
        method = request.method.lower()
        if method in self.routes:
            methodview = self.routes[method]
            if not methodview:
                return self.http_method_not_allowed(request, *args, **kwargs)
            if (dict == type(methodview)):
                if (methodview.get('useit', None)):
                    return self.get_xview(methodview['view'], request, *args, **kwargs)
                return self.http_method_not_allowed(request, *args, **kwargs)
            return self.get_xview(methodview, request, *args, **kwargs)
        return self.http_method_not_allowed(request, *args, **kwargs)



    def get_xview(self, view, request, *args, **kwargs):
        if (inspect.isclass(view)):
            xview = view.as_view()
            xview.routes = self.routes
            return xview(request, *args, **kwargs)
        res = None
        try:
            res = view(request, *args, **kwargs)
        except TemplateDoesNotExist:
            res = self.http_method_not_found(request, *args, **kwargs)
            
        return res
