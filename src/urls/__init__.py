# -*- coding: utf-8 -*-



import django.conf.urls

from django.conf.urls import patterns, url, include

from apps.genapi.urls import suffixes
from apps.genapi.views.hmdv import Hmdv



def url(*args, **kwargs):
    url = django.conf.urls.url(*args, **kwargs)
    return url

def patterns(*args, **kwargs):
    urlpatterns = django.conf.urls.patterns(*args, **kwargs)
    return urlpatterns

def sxpatterns(*args, **kwargs):
    urlpatterns = django.conf.urls.patterns(*args, **kwargs)
    urlpatterns = suffixes.format(urlpatterns)
    return urlpatterns

def include(*args, **kwargs):
    return django.conf.urls.include(*args, **kwargs)


def urlcrud_name(mod, name = None):
    if(name):
        return name
    return mod.__name__.split('.')[-1]


def urlcrud(mod, modname = None, *args, **kwargs):
    urlpatterns = []

    _modname = urlcrud_name(mod, modname)

    ##
    ## Используется Hmdv.as_view(),
    ## для использования разных контроллеров
    ## по разным HTTP-запросам
    ##

    urlpatterns += patterns('',
        url(
            r'^/$',
            Hmdv.as_view(),
            name= mod.__name__  + '.list',
            kwargs = {
                'routes' : {
                    'get':  mod.List
                        if hasattr(mod, 'List') else None,
                    'post': mod.Create
                        if hasattr(mod, 'Create') else None,
                    'delete': mod.Destroy
                        if hasattr(mod, 'Destroy') else None
                }
            }
        )
    )



    urlpatterns += patterns('',
        url(
            r'^/(?P<pk>.+)/file/$',
            Hmdv.as_view(),
            name= mod.__name__  + '.file',
            kwargs = {
                'routes' : {
                    'get': mod.File
                        if hasattr(mod, 'File') else None,
                    'put': mod.File
                        if hasattr(mod, 'File') else None,
                    'post': mod.File
                        if hasattr(mod, 'File') else None
                }
            }
        )
    )


    urlpatterns += patterns('',
        url(
            r'^/(?P<pk>.+)/copy/$',
            Hmdv.as_view(),
            name= mod.__name__  + '.file',
            kwargs = {
                'routes' : {
                    'get': mod.Copy
                        if hasattr(mod, 'Copy') else None,
                    'post': mod.Copy
                        if hasattr(mod, 'Copy') else None,
                }
            }
        )
    )

    urlpatterns += patterns('',
        url(
            r'^/(?P<pk>.+)/$',
            Hmdv.as_view(),
            name= mod.__name__  + '.detail',
            kwargs = {
                'routes' : {
                    'get': mod.Detail
                        if hasattr(mod, 'Detail') else None,
                    'put': mod.Detail
                        if hasattr(mod, 'Detail') else None,
                    'post': mod.Detail
                        if hasattr(mod, 'Detail') else None,
                    'patch': mod.Detail
                        if hasattr(mod, 'Detail') else None,
                    'delete': mod.Destroy
                        if hasattr(mod, 'Destroy') else None
                }
            }
        )
    )

    if(hasattr(mod, 'Home')):
        urlpatterns += patterns('',
            url(
                r'^/$',
                mod.Home.as_view(),
                name='Home'
            )
        )

    if(hasattr(mod, 'ListPart')):
        urlpatterns += patterns('',
            url(
                r'^/part/$',
                mod.ListPart.as_view(),
                name='listpart'
            )
        )

    return url(
        r'^' + _modname,
        include(urlpatterns, namespace = _modname)
    )
