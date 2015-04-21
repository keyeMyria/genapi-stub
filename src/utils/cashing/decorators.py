# -*- coding: utf-8 -*-


from  django.core.cache import cache as default_cache
from  django.core.cache import get_cache

import pickle
import inspect, itertools

from  collections import OrderedDict
from  collections import Hashable


import logging
import time
import os
import thread
import inspect


import string
BASE_LIST = string.digits + string.letters + '_@'
BASE_DICT = dict((c, i) for i, c in enumerate(BASE_LIST))

def base_decode(string, reverse_base=BASE_DICT):
    length = len(reverse_base)
    ret = 0
    for i, c in enumerate(string[::-1]):
        ret += (length ** i) * reverse_base[c]

    return ret

def bex(integer, base=BASE_LIST):
    length = len(base)
    ret = ''
    while integer != 0:
        ret = base[integer % length] + ret
        integer /= length

    return ret




class CallCacherUndefined(object):
    pass

DEFAULT_TIMEOUT = object()

class BaseCallCacher(object):

    def __init__(self, initname = None,  cache = None, cachename = None, timeout = DEFAULT_TIMEOUT, args = []):
        self.initname = 'anon'
        self.cashe = None
        if (cachename):
            self.cashe = get_cache(cachename)
        if (initname):
            self.initname = initname
            if(not self.cashe):
                self.cashe = get_cache(self.initname)
        if (not cache):
            self.cashe = default_cache
        self.timeout = timeout
        if(DEFAULT_TIMEOUT == self.timeout):
            self.timeout = self.cashe.default_timeout
        self.args = args
        self.logger = logging.getLogger('apps.genapi.basecallcacher')


    def fun_class(self, function, args, kwargs):
        if(len(args) > 0 and inspect.isclass(args[0])):
            klass = args[0]
            return args[0]
        return None

    def fun_name(self, function, args, kwargs):
        name = function.__name__
        klass = self.fun_class(function, args, kwargs)
        if(klass):
            name = "%s %s"%(klass.__name__, name)

        return "%s"%(name)

    def log_set(self, name):
        pass
        #self.logger.debug("fun set = %s"%(name))

    def log_hit(self, name):
        pass
        #self.logger.debug("fun hit = %s"%(name))

    def log_ans(self, name):
        pass
        #self.logger.debug("fun ans = %s"%(name))


    def build_key(self, function, args = (), kwargs = {}, callname = None):
        funid = str(function)
        klass = self.fun_class(function, args, kwargs)
        klid = str(klass)
        cargs = self.cacheable_args(function, args, kwargs)
        gid = os.getpid()
        tid = thread.get_ident()
        key = hash((
            gid,
            tid,
            self.initname,
            callname,
            klid,
            funid,
            cargs
        ))
        return key


    def cacheable_args(self, function, args = (), kwargs = {}):
        return (str(args), str(kwargs))

    def __2_cacheable_args(self, function, args = (), kwargs = {}):
        a1 = tuple([str(a) for a in args])
        a2 = tuple([(str(k), str(v)) for k, v in kwargs.items()])
        return (a1, a2)

    def __1_cacheable_args(self, function, args = (), kwargs = {}):
        args_name = list(
            OrderedDict.fromkeys(
                inspect.getargspec(function)[0] + kwargs.keys()
            )
        )
        args_dict = OrderedDict(
            list(itertools.izip(args_name, args)) + list(kwargs.items())
        )
        return (tuple(args_dict.keys()), tuple(args_dict.values()))

    def set(self, function, args = (), kwargs = {}, callname = None, version=None, *xarg, **xkwargs):
        fn = self._set(function, callname, version, *xarg, **xkwargs)
        return fn(*args, **kwargs)

    def reset(self, function, args = (), kwargs = {}, callname = None, version=None, *xarg, **xkwargs):
        fn = self._set(function, callname, version, reset=True, *xarg, **xkwargs)
        return fn(*args, **kwargs)

    def __call__(self, function, callname = None, version=None, *xarg, **xkwargs):
        return self._set(function, callname, version, *xarg, **xkwargs)



class CallCacher(BaseCallCacher):

    def __init__(self, *args, **kwargs):
        super(CallCacher, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('apps.genapi.callcacher')

    def _set(self, function, callname = None, version=None, reset=False, *xarg, **xkwargs):
        decorator_self = self
        def _function(*args, **kwargs):
            funname = self.fun_name(function, args, kwargs)
            self.log_hit(funname)
            key = self.build_key(
                function = function,
                args     = args,
                kwargs   = kwargs,
                callname = callname
            )
            if(not reset):
                result = decorator_self.cashe.get(
                    key     = key,
                    default = CallCacherUndefined,
                    version = version,
                )
                if(result != CallCacherUndefined):
                    self.log_ans(funname)
                    return result
            result = function(*args, **kwargs)
            decorator_self.cashe.set(
                key     = key,
                value   = result,
                timeout = decorator_self.timeout,
                version = version
            )
            self.log_set(funname)
            return result
        return _function


class InternalCallCacher(BaseCallCacher):

    def __init__(self, *args, **kwargs):
        super(InternalCallCacher, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('apps.genapi.internalcallcacher')

    def _set(self, function, callname = None, version=None, reset=False, *xarg, **xkwargs):
        decorator_self = self
        if(not hasattr(function, 'cache')):
            function.cache = dict()
        function.cache_expired_time = 0
        def _function(*args, **kwargs):
            funname = self.fun_name(function, args, kwargs)
            self.log_hit(funname)
            now = time.time()
            function.cache_expired_time = now + decorator_self.timeout
            key = self.build_key(
                function = function,
                args     = args,
                kwargs   = kwargs,
                callname = callname
            )
            actual = True
            if(decorator_self.timeout):
                actual = (function.cache_expired_time > now)
            if ((not reset) and actual):
                result = function.cache.get(key, CallCacherUndefined)
                if(result != CallCacherUndefined):
                    self.log_ans(funname)
                    return result
            result = function(*args, **kwargs)
            function.cache[key] = result
            decorator_self.cashe.set(
                key     = key,
                value   = result,
                timeout = decorator_self.timeout,
                version = version
            )
            self.log_set(funname)
            return result
        return _function
