 # -*- coding: utf-8 -*-

import futures

class PoolExecutor():
    __executor  = None
    __MAX_WORKERS__ = 100
    def __init__(self, *args, **kvargs):
        if(not self.__executor):
            self.__executor = futures.ThreadPoolExecutor(self.__MAX_WORKERS__)

    def map(self, function, iterable, *args, **kvargs):
        return self.__executor.map(function, iterable)
