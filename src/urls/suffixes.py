# -*- coding: utf-8 -*-

from django.core.urlresolvers import RegexURLResolver
from django.conf.urls import patterns, url, include

from django.template.loader import get_template

from rest_framework import permissions, renderers, viewsets
from rest_framework.settings import api_settings
from rest_framework.response import Response


from django.conf import settings
from django.http import Http404
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

import functools

import os
import copy


from apps.genapi.views.hmdv import Hmdv



def tresponse(function):
    '''
        Adds `rest_framework.response.Response` with two parametrs
        to initial function.
            The first one is data of initial response.
            The second one is the path to template.
            This path can be described in View class attributes.
            If it is not path calculates like this:
                /<app_name>/<model_name>/<class_name>.html.djt

        @param function is a method of View class,
                        which we want to decorate.
    '''
    if(not hasattr(function, 'has_tresponse')):
        def _internal(self, request, *args, **kwargs):
            response = function(self, request, *args, **kwargs)
            _template_name = None
            if(hasattr(self, 'template_name')):
                _template_name = self.template_name
            else:
                _template_name = construct_template_name(self)


            ##
            ## We cannot use normal Django Middleware,
            ## cause we deal with Rest_framework request and response.
            ## (not Django's request\response)
            ##
            if request.accepted_renderer.format == 'html':
                try:
                    print "_template_name = ",  get_template(_template_name)
                except TemplateDoesNotExist:
                    raise Http404

                page = request.GET.get('page', 1);
                search = request.GET.get('search', "");
                response = Response(
                    {
                        'data': response.data,
                        'meta': {
                            'settings': settings,
                            'request':  request,
                            'page':     page,
                            'search':   search
                        }
                    },
                    template_name=_template_name
                )
            #if(not response.data.get('meta')):
                #response.data['meta'] = {}
            #response.data['meta']['settings'] = settings
            return response
        _internal.has_tresponse = True
        return _internal
    else:
        return function


def construct_template_name(ctl):
    app_label = "index"
    ctl_group = "index"
    ctl_cls  = ctl.__class__.__name__.lower()
    if(hasattr(ctl, 'model') and ctl.model != None):
        app_label = ctl.model._meta.app_label.lower()
        ctl_group = ctl.model.__name__.lower()
    else:
        if(hasattr(ctl, 'app_label') and ctl.app_label != None):
            app_label = ctl.app_label.lower()
        if(hasattr(ctl, 'ctl_group') and ctl.ctl_group != None):
            ctl_group = ctl.ctl_group.lower()
    return  ".".join(
        [
            os.sep.join([app_label, ctl_group, ctl_cls]),
            "html.djt"
        ]
    )

def apply_suffix_patterns(urlpatterns, suffix_pattern):
    def _lambda(acc, urlpattern):
        return apply_suffix_pattern(
            acc,
            urlpattern,
            suffix_pattern
        )
    return functools.reduce(_lambda, urlpatterns, [])

def apply_suffix_pattern(acc, urlpattern, suffix_pattern):
    if isinstance(urlpattern, RegexURLResolver):
        return apply_suffix_pattern_cached(
            acc,
            urlpattern,
            suffix_pattern
        )
    else:
        return apply_suffix_pattern_plain(
            acc,
            urlpattern,
            suffix_pattern
        )

def apply_suffix_pattern_cached(acc, urlpattern, suffix_pattern):
    regex = urlpattern.regex.pattern
    namespace = urlpattern.namespace
    app_name = urlpattern.app_name
    kwargs = urlpattern.default_kwargs
    patterns = apply_suffix_patterns(
        urlpattern.url_patterns,
        suffix_pattern
    )
    acc.append(
        url(
            regex,
            include(
                patterns,
                namespace,
                app_name
            ),
            kwargs
        )
    )
    return acc;

def patch_class(clobj):
    for method in ['get', 'put', 'post', 'delete', 'patch']:
        if (hasattr(clobj, method)):
            setattr(clobj, method, tresponse(getattr(clobj, method)))
    return clobj

def apply_suffix_pattern_plain(acc, urlpattern, suffix_pattern):
    regex = urlpattern.regex.pattern.rstrip('/$') + suffix_pattern
    view = urlpattern._callback or urlpattern._callback_str
    kwargs = urlpattern.default_args
    name = urlpattern.name
    viewclass = patch_class(view.cls)

    if viewclass == Hmdv:
        routes = kwargs.get('routes', None)
        xroutes = {}
        del kwargs['routes']
        acc.append(url(
            regex,
            viewclass.as_view(
                routes = routes
            ),
            kwargs,
            name
        ))

        for route in routes:
            if(routes[route]):
                xroutes[route] = patch_class(routes[route]).as_view(
                    renderer_classes=(
                        renderers.TemplateHTMLRenderer,
                    )
                )

        acc.append(
            url(
                urlpattern.regex.pattern,
                viewclass.as_view(
                    routes = xroutes,
                    renderer_classes=(
                        renderers.TemplateHTMLRenderer,
                    )
                ),
                kwargs,
                name
            )
        )
    else:
        acc.append(url(regex, view, kwargs, name))
        acc.append(
            url(
                urlpattern.regex.pattern,
                viewclass.as_view(
                    renderer_classes=(
                        renderers.TemplateHTMLRenderer,
                    )
                ),
                kwargs,
                name
            )
        )
    return acc

def format(
    urlpatterns,
    allowed=['json', 'jsonp', 'html', 'xml', 'csv',  'xlsx', 'yaml', 'api']
):
    suffix_kwarg = api_settings.FORMAT_SUFFIX_KWARG
    if allowed:
        if len(allowed) == 1:
            allowed_pattern = allowed[0]
        else:
            allowed_pattern = '(%s)' % '|'.join(allowed)
            suffix_pattern = r'\.(?P<%s>%s)$' % (
                suffix_kwarg,
                allowed_pattern
            )
    else:
        suffix_pattern = r'\.(?P<%s>[a-z]+)$' % suffix_kwarg
    return apply_suffix_patterns(urlpatterns, suffix_pattern)
