# -*- coding: utf-8 -*-

import copy
import itertools
import sys
from datetime import datetime

from django.utils.six import with_metaclass

from django.utils import six
from django.db.models import Q

from django.db import ProgrammingError

from apps.genapi.utils.log.logmeta import LogMeta

from apps.genapi.src.utils import toint

from .queryset import QuerySet

import logging

MAX_GET_RESULTS = 2


class MultiQuerySetExpression(ProgrammingError):
    pass

class MultiQuerySet(QuerySet, with_metaclass(LogMeta)):

    logger = logging.getLogger('django.db.backends')

    def __init__(self, querysetdict = None, *args, **kwargs):
        self.querysetdict = querysetdict
        if(self.querysetdict):
            self._x_model = querysetdict[querysetdict.keys()[0]].model
            super(MultiQuerySet, self).__init__(
                model = None,
                *args,
                **kwargs
            )
            #self.poolexecutor = PoolExecutor()



    def __and__(self, other):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            if(isinstance(other, self.__class__)):
                clone.querysetdict[number] = qs & other.querysetdict[number]
        return clone


    def __or__(self, other):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            if(isinstance(other, self.__class__)):
                clone.querysetdict[number] = self.querysetdict[number] | other.querysetdict[number]
            if(isinstance(other, QuerySet)):
                if(other._db == qs._db):
                    clone.querysetdict[number] = self.querysetdict[number] | other
        return clone

    def str_sql(self):
        return {
            number: qs.str_sql()
            for number, qs in six.iteritems(self.querysetdict)
        }

    def none(self):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            clone.querysetdict[number] = qs.none()
        return clone

    def order_by(self, *args, **kwargs):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            clone.querysetdict[number] = qs.order_by(*args, **kwargs)
        return clone

    def values(self, *args, **kwargs):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            clone.querysetdict[number] = qs.values(*args, **kwargs)
        return clone


    def annotate(self, value, *args, **kwargs):
        clone = self._clone()
        for number, qs in six.iteritems(clone.querysetdict):
            clone.querysetdict[number] = qs.annotate(*args, **kwargs)
        return clone

    def group_by(self, value, *args, **kwargs):
        res = []
        for number, qs in six.iteritems(self.querysetdict):
            res += [r for r in qs.values(value).annotate(*args, **kwargs)]

        return res

    def _filter_or_exclude_on_baseno(self, baseno, negate, *args, **kwargs):

        baseno = toint(baseno)
        if(None == baseno or None == self.querysetdict.get(baseno)):
            mqse = MultiQuerySetExpression("wrong baseno")
            mqse.__cause__ = "wrong baseno"
            self.logger.error("wrong baseno = '%s'"%(baseno))
            raise mqse


        query = self.querysetdict[baseno]._clone();
        res = query._filter_or_exclude(negate, *args, **kwargs)
        return res


    def __iter__(self):
        #return (self[item] for item in range(self._count()))
        self._fetch_all()
        return iter(self._result_cache)

    def sall(self, karg):

        newquerysetdict = []
        for number, qs in six.iteritems(self.querysetdict):
            newquerysetdict += qs[start:stop:step]


    def __getitem__(self, karg):
        '''
            @TODO 1:
                May be it necessary to use `PoolExecutor` there.        #if( hasattr(self._x_model, 'baseno') ):
            #self._x_model.baseno = baseno

        #query = self.querysetdict[baseno]._clone();

        #query.model.baseno = baseno

                But, we cannot use it, in simple way like in map.
            @TODO 2:
                Add operation for one-instance-slice
        '''
        newquerysetdict = []
        acc = 0
        for number, qs in six.iteritems(self.querysetdict):
            qs.__count_val = qs.count()
            qs.start = acc
            acc += qs.__count_val
            qs.stop  = acc
            if isinstance(karg, slice):
                start = None
                stop  = None
                step  = None
                if karg.start is not None:
                    start = int(karg.start)
                else:
                    start = 0
                if karg.stop is not None:
                    stop = int(karg.stop)
                else:
                    stop = qs.__count_val
                if karg.step is not None:
                    step = int(karg.step)
                else:
                    step = 1
                if(qs.start <= start < qs.stop):
                    if(qs.start < stop <= qs.stop):
                        '''
                        [1, 2, 3, 4] *[5, 6, 7, 8]* [9, A, B, C, D]
                                          ^__^
                        '''
                        start = start - qs.start
                        stop  = stop  - qs.start
                        newquerysetdict += qs[start:stop:step]
                    elif(stop > qs.stop):
                        '''
                        *[1, 2, 3, 4]* [5, 6, 7, 8] [9, A, B, C, D]
                             ^_____________^
                        '''
                        start = start - qs.start
                        stop = qs.__count_val
                        newquerysetdict += qs[start:stop:step]
                elif(start < qs.start):
                    if(qs.start < stop <= qs.stop):
                        '''
                        [1, 2, 3, 4] *[5, 6, 7, 8]* [9, A, B, C, D]
                            ^_____________^
                        '''
                        start = 0
                        stop  = stop - qs.start
                        newquerysetdict += qs[start:stop:step]
                    elif(qs.stop < stop):
                        '''
                        [1, 2, 3, 4] *[5, 6, 7, 8]* [9, A, B, C, D]
                            ^______________________________^
                        '''
                        start = 0
                        stop = qs.__count_val
                        newquerysetdict += qs[start:stop:step]
                elif ((qs.stop <= start) and (qs.start < start)):
                    '''
                    *[1, 2, 3, 4]* [5, 6, 7, 8] [9, A, B, C, D]
                                       ^__^
                    '''
                    pass
                elif ((start < qs.start) and  (stop <= qs.start)):
                    '''
                    [1, 2, 3, 4] *[5, 6, 7, 8]* [9, A, B, C, D]
                         ^__^
                    '''
                    pass
        if isinstance(karg, slice):
            return newquerysetdict

        return self[karg:karg+1][0]

    def _clone(self, klass=None, setup=False, **kwargs):
        for basseno, queryset in six.iteritems(self.querysetdict):
            queryset = queryset._clone(
                klass=None,
                setup=False,
                **kwargs
            )

        c = self.__class__(querysetdict=self.querysetdict)
        c._x_model = self._x_model
        return c

    def _fetch_all_by_query(self, query):
        __result_cache = list(query)
        return __result_cache

    def _fetch_all(self):
        t1 = datetime.now()
        res = map(
            self._fetch_all_by_query,
            self.querysetdict.values()
        )
        t2 = datetime.now()
        d = t2 - t1
        self._result_cache = sum(
            res,
            []
        )
        t2 = datetime.now()
        d = t2 - t1

    def _filter_or_exclude(self, negate, *args, **kwargs):
        print "1";
        return self._filter_or_exclude_multi(negate, *args, **kwargs)

    def _filter_or_exclude_multi(self, negate, *args, **kwargs):
        clone = self._clone()
        if negate:
            for index, queryset in six.iteritems(clone.querysetdict):
                q = queryset.query
                fkwargs = self.__filter_kwargs(q, kwargs)
                q.add_q(~Q(*args, **fkwargs ))
        else:
            for index, queryset in six.iteritems(clone.querysetdict):
                q = queryset.query
                fkwargs = self.__filter_kwargs(q, kwargs)
                q.add_q(Q(*args, **fkwargs))
        return clone


    def __filter_kwargs(self, query, kwargs):
        return kwargs


    def __count_by_query(self, query):
        res = query.count()
        return res

    def _count(self):
        res = map(
            self.__count_by_query,
            self.querysetdict.values()
        )
        return sum(list(res))

    def count(self):
        return self._count()


    def get(self, *args, **kwargs):
        """
        Performs the query and returns a single object matching the given
        keyword arguments.
        """
        clone = self.filter(*args, **kwargs)
        if self.query.can_filter():
            clone = clone.order_by()
        clone = clone[:MAX_GET_RESULTS + 1]
        num = len(clone)
        if num == 1:
            return clone[0]
        if not num:
            raise self._x_model.DoesNotExist(
                "%s matching query does not exist." %
                self._x_model._meta.object_name)
        raise self._x_model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!" % (
                self._x_model._meta.object_name,
                num if num <= MAX_GET_RESULTS else 'more than %s' % MAX_GET_RESULTS
            )
        )

