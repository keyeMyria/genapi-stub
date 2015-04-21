 # -*- coding: utf-8 -*-

import logging

import johnny.cache

from apps.genapi.utils.cashing.decorators import CallCacher, InternalCallCacher

from .common import Common

from .manager import Manager

class SmartDictUndefined(object):
    pass

class BaseDict(dict):
    kesc = SmartDictUndefined

class SmartDict(BaseDict):
    redict = None
    def __getitem__(self, *args, **kwargs):
        return self.get(*args, **kwargs)
    def get(self, k, d = None, useredict=True, *args, **kwargs):
        res = d
        redict = self.redict
        if(None == redict or k == self.kesc or not useredict):
            res = super(SmartDict, self).get(k, d)
        else:
            res = super(SmartDict, self).get(k, SmartDictUndefined)
            if (res == SmartDictUndefined):
                self = self.__class__(redict(self))
                res = self.get(k, d)
        return res


class Handbook(Common):

    objects = Manager()

    _call_cacher = CallCacher('handbook_cacher')
    _logger = logging.getLogger('apps.genapi.handbook')

    @classmethod
    @InternalCallCacher('handbook_cacher')
    def dict(cls, **kwargs):
        return BaseDict(super(Handbook, cls).dict(**kwargs))

    @classmethod
    @InternalCallCacher('handbook_cacher')
    def list(cls, **kwargs):
        return super(Handbook, cls).list(**kwargs)

    @classmethod
    @InternalCallCacher('handbook_get_cacher')
    def get(cls, item = None, default = None, **kwargs):
        _dct = cls.dict(**kwargs)
        res = _dct.get(item, default)
        return res

    @classmethod
    def smart_dict(cls, **kwargs):
        fn = super(Handbook, cls).dict
        return cls._dict(fn, **kwargs)

    @classmethod
    def _dict(cls, fn, **kwargs):
        res = cls._call_cacher.set(fn, kwargs=kwargs, callname = cls)
        sd = SmartDict(res)
        def sdredict(x):
            johnny.cache.disable()
            res = cls._call_cacher.reset(fn, kwargs=kwargs, callname = cls)
            cls._logger.debug("_dict %s"%(cls.__name__))
            johnny.cache.enable()
            return SmartDict(res)
        sd.redict = sdredict
        return sd


    def save(self, *args, **kwargs):
        return super(Handbook, self).save(*args, **kwargs)







    class Meta:
        abstract = True
