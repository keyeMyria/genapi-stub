
import os
import six
import sys
import logging
import platform
import types

class LogMixin():
    def __init__(self, *args, **kwargs):
        for attr_name, attr_value in six.iteritems(vars(self)):
            #attr_value = getattr(self.__class__, attr)
            if isinstance(attr_value, types.FunctionType):
                attr_value = self.decoreate(self.__class__, attr_value)
                setattr(self.__class__, attr_value)


    def decoreate(self, name, func):
        def wrapper(*args, **kwargs):
            logging.debug("<BEFORE %s %s.%s(%s) />"%(func.im_class(), name, func.func_name,kwargs))
            res = func(*args, **kwargs)
            logging.debug("<AFTER  %s %s.%s(%s) />"%(func.im_class(), name, func.func_name, kwargs))
            return res
        return wrapper

