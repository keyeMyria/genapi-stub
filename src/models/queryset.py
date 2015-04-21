# -*- coding: utf-8 -*-

import copy
import itertools
import sys
from datetime import datetime

from django.utils.six import with_metaclass

from django.utils import six
import django.db.models.query

from django.db.models import sql

from apps.genapi.utils.log.logmeta import LogMeta

from caching.base import CachingManager, CachingMixin, CachingQuerySet

from django.db.models import signals

import six


from .fields import BigIntegerField
from .fields import CharField
from .fields  import SetField
from .fields import DateTimeField
from .fields import DecimalField
from .fields import FloatField
from .fields import IntegerField
from .fields import TextField

#class QuerySet(CachingQuerySet, with_metaclass(LogMeta)):

class QuerySet(django.db.models.query.QuerySet, with_metaclass(LogMeta)):
    '''

        См. http://ramenlabs.com/2010/12/08/how-to-quack-like-a-queryset/
    '''
    def str_sql(self):
        return str(self.query)

    def pre_save_send(self, obj = None, update_fields=None):
        instance = obj
        if(instance):
            origin = self.model
            table = origin._meta.db_table
            signals.pre_save.send(
                sender=origin,
                instance=instance,
                table=table,
                update_fields=update_fields,
                raw=False,
                using=self.db
            )

    def post_save_send(self, obj = None, created = False, updated=False):
        if(created or updated):
            instance = obj
            if(instance):
                origin = self.model
                table = origin._meta.db_table
                signals.post_save.send(
                    sender=origin,
                    instance=instance,
                    table=table,
                    created=created,
                    raw=False,
                    using=self.db
                )


    def post_delete_send(self, obj):
        instance = obj
        if(instance):
            origin = self.model
            table = origin._meta.db_table
            signals.post_save.send(sender=origin, instance=instance,
                                    table=table, created=True, raw=False, using=self.db)
            signals.post_delete.send(
                sender=instance, instance=origin, using=self.db
            )


    def bulk_create(self, objs, *args, **kwargs):
        res = super(QuerySet, self).bulk_create(objs, *args, **kwargs)
        [self.post_save_send(obj = obj, created = True) for obj in objs]
        return res

    def create(self, *args, **kwargs):
        obj = super(QuerySet, self).create(*args, **kwargs)
        self.post_save_send(created = True, obj=obj)
        return obj


    def update(self, *args, **kwargs):
        res = super(QuerySet, self).update(*args, **kwargs)
        [self.post_save_send(obj = obj, updated = True) for obj in self.all()]
        return res


    def delete(self, *args, **kwargs):
        res = super(QuerySet, self).delete(*args, **kwargs)
        [self.post_delete_send(obj=obj) for obj in self.all()]
        return res

    def raw(self, raw_query, params=None, *args, **kwargs):
        return django.db.models.query.RawQuerySet(
            raw_query=raw_query,
            model=self.model,
            params=params,
            using=self.db,
            *args,
            **kwargs
        )


    def _insert_query(self,
            model,
            objs,
            fields,
            return_id=True,
            raw=False,
            using=None,
            update = [],
            replace = False,
            ignore = False,
        ):

        query = sql.InsertQuery(model)
        query.insert_values(fields, objs, raw=raw)
        compiler = query.get_compiler(using=using)

        post_str = ''
        if(update):
            xupdate = self._build_update(fields, update)
            if(xupdate):
                update_str = ','.join([
                    "`%s` = %s"%(key,value)
                    for key, value in six.iteritems(xupdate)
                ])
                post_str = 'on duplicate key update %s'%(update_str)
        pre_replace_str = ''

        if(replace):
            pre_replace_str = 'REPLACE'

        if(ignore):
            pre_replace_str = 'INSERT IGNORE'

        return self._insert_query_execute_sql(
            compiler = compiler,
            return_id = return_id,
            pre_replace_str = pre_replace_str,
            post_str = post_str
        )


    def _build_update(self, fields, update):
        xupdate = {}
        for fname in update:
            for field in fields:
                _xupdate = self._build_update_field(field, fname)
                xupdate.update(_xupdate)
        return xupdate

    def _build_update_field(self, field, fname):
        '''
            Для одного поля формирует строку, которая идет в запросе после
                on duplicate key update
        '''
        xupdate = {}
        column = field.db_column
        if(type(fname) == str):
            if (field.name == fname):
                xupdate[column] = 'values(`%s`)'%(column)
        elif type(fname) == tuple:
            if (len(fname) > 1) and (field.name == fname[0]):
                opvalue = fname[1]
                if(type(opvalue) == str):
                    xupdate[column] = '%s'%(fname[1])
                if(type(opvalue) == tuple):
                    if (len(fname) > 1):
                        op = opvalue[0]
                        val = opvalue[1]
                        if ('+' == op):
                            if(type(val) != list):
                                val = [str(val)]

                            if (isinstance(field,SetField)):
                                xupdate[column] = "CONCAT_WS(',',`%s`, '%s')"%(
                                        field.db_column,
                                        ','.join(val)
                                    )

                            elif (isinstance(field,CharField)
                                  or isinstance(field,TextField)):
                                xupdate[column] = "CONCAT_WS('',`%s`, '%s')"%(
                                        field.db_column,
                                        ''.join(val)
                                    )

                            elif (isinstance(field,IntegerField)
                                  or isinstance(field,BigIntegerField)
                                  or isinstance(field,FloatField)
                                  or isinstance(field,DecimalField)):
                                xupdate[column] = "%s + `%s`"%(
                                        field.db_column,
                                        '+'.join(val)
                                    )

        return xupdate



    def _insert_query_execute_sql(self,
            compiler,
            return_id=False,
            pre_replace_str = None,
            post_str = None
        ):
        #assert not (return_id and len(compiler.query.objs) != 1)
        compiler.return_id = return_id
        cursor = compiler.connection.cursor()
        for sql, params in compiler.as_sql():

            if(pre_replace_str):
                sql = sql.replace('INSERT', pre_replace_str)

            if(post_str):
                sql += (' %s'%(post_str));

            print "cursor.execute(sql, params) %s %s"%(sql, params)
            
            cursor.execute(sql, params)
        if not (return_id and cursor):
            return
        if compiler.connection.features.can_return_id_from_insert:
            return compiler.connection.ops.fetch_returned_insert_id(cursor)
        return compiler.connection.ops.last_insert_id(cursor,
                compiler.query.get_meta().db_table, compiler.query.get_meta().pk.column)


    def _raw_insert(self,
            objs = [],
            fields = None,
            update = [],
            replace = False,
            ignore=False,
        ):
        if(not fields):
            fields = self.model._meta.fields

        if (type(objs) != list):
            objs = [objs]

        for obj in objs:
            self.pre_save_send(obj = obj, update_fields = update)

        res = self._insert_query(
            self.model,
            objs,
            fields,
            using=self.db,
            update = update,
            replace = replace,
            ignore = ignore,
        )


        usecreate = (update == [])

        useupdate = not (update == [])

        for obj in objs:
            self.post_save_send(obj = obj, created = usecreate, updated = useupdate)

        return res

    def insert(self, objs, fields = None):
        return self._raw_insert(
            objs,
            fields,
            update = [],
            replace = False,
            ignore = False,
        )


    def insert_update(self, objs, fields = None, update=None):
        if(None == update):
            update = [field.name for field in self.model._meta.fields]

        return self._raw_insert(
            objs,
            fields,
            update = update,
            replace = False,
            ignore = False,
        )

    def insert_ignore(self, objs, fields = None):
        return self._raw_insert(
            objs,
            fields,
            update = [],
            replace = False,
            ignore = True,
        )

    def replace(self, objs, fields = None):
        return self._raw_insert(
            objs,
            fields,
            update = [],
            replace = True,
            ignore = False,
        )



    def __and__(self, other):
        if(other.__module__ == 'apps.genapi.models.multiqueryset'):
            return other & self
        return super(QuerySet, self).__and__(other);

    def __or__(self, other):
        if(other.__module__ == 'apps.genapi.models.multiqueryset'):
            return other | self
        return super(QuerySet, self).__or__(other);
	

