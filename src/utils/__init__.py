import time
from datetime import datetime

from collections  import OrderedDict
from bisect import bisect_left, insort

import copy

from itertools import groupby


from django.utils.datastructures import SortedDict

import uuid
import hashlib
import struct


class combimethod(object):
    def __init__(self, func):
        self._func = func
    def classmethod(self, func):
        self._classfunc = classmethod(func)
        return self
    def __get__(self, instance, owner):
        if instance is None:
            return self._classfunc.__get__(instance, owner)
        else:
            return self._func.__get__(instance, owner)



def md5unit64(string):
    digest = hashlib.md5(string.encode('utf-8')).digest()
    ar = struct.unpack(">IIII", digest)
    hig = ar[1] ^ ar[3]
    low = ar[0] ^ ar[2]
    return (hig << 32 | low)


def get_or_none(klass, *args, **kwargs):
    queryset = klass.objects.all()
    res = queryset.filter(*args, **kwargs)
    return res[0] if res else None


def cached_get_or_none(klass, use_cache=True, *args, **kwargs):
    if(use_cache):
        _items = kwargs.items()
        if(_items):
            pk = _items[0][1]
            return klass.get(pk)
        return None
    return get_or_none(klass, *args, **kwargs)


def deepcopy(*args, **kwargs):
    return copy.deepcopy(*args, **kwargs)

def unique(a):
    seen = set()
    return [seen.add(x) or x for x in a if x not in seen]

def unique_(a):
    return OrderedDict.fromkeys(a).keys()

def dedup(seq):
    """
        Remove duplicates. Preserve order first seen.
        Assume orderable, but not hashable elements
    """
    result = []
    seen = []
    for x in seq:
        i = bisect_left(seen, x)
        if i == len(seen) or seen[i] != x:
            seen.insert(i, x)
            result.append(x)
    return result

def tofloat(a, default = None):
    if(None == a):
        return default
    if isinstance(a, float):
        return a
    try:
        return float(a)
    except:
        return default
    return default


def check_isdigit(s):
    if len(s) and s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def toint(a, default = None):
    if(None == a):
        return default
    if isinstance(a, int):
        return a
    if isinstance(a, str) or isinstance(a, unicode):
        if(not check_isdigit(a)):
            return default
    try:
        return int(a)
    except:
        return default
    return default


def tolong(a, default = None):
    if(None == a):
        return default
    if isinstance(a, long):
        return a
    if isinstance(a, str) or isinstance(a, unicode):
        if(not check_isdigit(a)):
            return default
    try:
        return long(a)
    except:
        return default
    return default



def tobool(val):
    if val == '':
        return True;
    if isinstance(val, str) or isinstance(val, unicode):
        val = val.lower()
    if val == 'false':
        return False;
    if val == 'true':
        return True;
    if val == 'no':
        return False;
    if val == 'yes':
        return True;
    if val == 'n':
        return False;
    if val == 'groupby_key_dict':
        return True;
    if val == 'f':
        return False;
    if val == 't':
        return True;
    return bool(val)


def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.utcfromtimestamp (epoch) - datetime.fromtimestamp(epoch)
    return utc + offset


def local2utc (local):
    epoch = time.mktime(local.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return local + offset


def utc2local_strunixtime (data = ""):
    data = toint(tofloat(data))
    if data == None:
        return None
    utc = datetime.fromtimestamp(data)
    local = utc2local(utc)
    data = time.mktime(local.timetuple())
    data = "%s"%(toint(data))
    return data


def local2utc_strunixtime  (data = ""):
    data = toint(tofloat(data))
    if data == None:
        return None
    local = datetime.fromtimestamp(data)
    utc = local2utc(local)
    data = time.mktime(utc.timetuple())
    data = "%s"%(toint(data))
    return data


import string
BASE_LIST = string.digits + string.letters + '_@'
BASE_DICT = dict((c, i) for i, c in enumerate(BASE_LIST))

def base_decode(string, reverse_base=BASE_DICT):
    length = len(reverse_base)
    ret = 0
    for i, c in enumerate(string[::-1]):
        ret += (length ** i) * reverse_base[c]

    return ret

def base_encode(integer, base=BASE_LIST):
    length = len(base)
    ret = ''
    while integer != 0:
        ret = base[integer % length] + ret
        integer /= length

    return ret


def dlist_sum_group(
    target_dlist,
    groupby_field_list = [],
    sum_field_list = [],
    field_list = [],
    convert = tolong,
):
    return dlist_agregate_group(
        agregate_function   = sum,
        target_dlist        = target_dlist,
        agregate_field_list = sum_field_list,
        field_list          = field_list,
        convert             = lambda x: tolong(x, 0)
    )


def dlist_agregate_group(
    agregate_function,
    target_dlist,
    groupby_field_list  = [],
    agregate_field_list = [],
    field_list          = [],
    convert             = lambda x: x
):

    if(not groupby_field_list):
        field_set          = set(field_list)
        field_set_for_sum  = set(agregate_field_list)
        field_set.difference_update(field_set_for_sum)
        groupby_field_list = list(field_set)


    def build_groupby_key_dict(item):
        return {
            field : item.get(field)
            for field in groupby_field_list
        }

    target_dlist = sorted(
        target_dlist,
        key = build_groupby_key_dict
    )

    prefetch = [
        (groupby_key_dict, list(for_agregate_generator))
        for groupby_key_dict, for_agregate_generator in groupby(
            target_dlist,
            key = build_groupby_key_dict
        )
    ]

    target_dlist = [
        SortedDict(
            groupby_key_dict.items()
            + [
                (
                    field,
                    agregate_function(convert(fa_dict.get(field, 0))
                        for fa_dict in for_agregate_dlist)
                )
                for field in agregate_field_list
            ]
        )
        for groupby_key_dict, for_agregate_dlist in prefetch
    ]
    return target_dlist
