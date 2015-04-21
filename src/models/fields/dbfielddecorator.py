# -*- coding: utf-8 -*-

import logging

from django.db import connections
from django.db import models

import decimal
from django.core import validators

from apps.genapi.utils import toint
from apps.genapi.utils import tofloat

DEFAULT_FIELDS_TIMEOUT_TIMES = 100

GET_DEFAULT_FROM_DB = 'get-default-from-db'

from django.core.validators import MaxValueValidator, MinValueValidator

def _fbyte_max(x, unsigned):
    return (2**(x*8-1)) * (unsigned + 1) -1

def _fbyte_min(x, unsigned):
    return - (2**(x*8-1)) * (1 - unsigned)

def fbyte_max(data_type, unsigned):
    return _fbyte_max(DATA_SIZES_VALIDATE[data_type], unsigned)

def fbyte_min(data_type, unsigned):
    return _fbyte_min(DATA_SIZES_VALIDATE[data_type], unsigned)


import struct

DATA_SIZES_VALIDATE = {
    'tinyint'   : 1,
    'smallint'  : 2,
    'mediumint' : 3,
    'int'       : 4,
    'bigint'    : 8,
}




class Undefined:
    pass

def fetchoneDict(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cursor.description ]
    return dict(zip(cols, row))

class DbFieldDecorator(object):

    def __call__(slf, dclass):

        class NewClass(dclass):
            def __init__(self, default = Undefined, *args, **kwargs):

                if Undefined == default:
                    default = GET_DEFAULT_FROM_DB

                dclass.__init__(
                    self,
                    default = default,
                    *args,
                    **kwargs
                )

            def pre_save(self, model_instance, add):
                res =  dclass.pre_save(self, model_instance, add)
                dbname = model_instance.__class__._default_manager.db
                if('default' != dbname):
                    con = connections[dbname]
                    xvalue = DbFieldDecorator.get_default_from_db(self, con, dbname)

                    ivalue = getattr(model_instance, self.name)
                    #self.validate(ivalue, model_instance)
                    if ((GET_DEFAULT_FROM_DB == ivalue) or (None == ivalue and not (self.null))):
                        setattr(model_instance, self.name, xvalue)
                return res

            def get_default(self):
                value = dclass.get_default(self)
                return self.to_python(value)

            def to_python(self, value):
                res = value
                if(GET_DEFAULT_FROM_DB == value):
                    if (not self.empty_strings_allowed):
                        res = None
                    else:
                        res =  ""
                return dclass.to_python(self, res)

            def get_prep_value(self, value):
                res = value
                if(GET_DEFAULT_FROM_DB == value):
                    if (not self.empty_strings_allowed or (self.null and
                            not connection.features.interprets_empty_strings_as_nulls)):
                       res = None
                    else:
                        res =  ""
                if isinstance(res, tuple):
                    res = res[0]
                return dclass.get_prep_value(self, res)

            def get_db_prep_value(self, value, connection, prepared=False):
                if(GET_DEFAULT_FROM_DB == value or (None == value and not (self.null))):
                    res = DbFieldDecorator.get_default_from_db(self, connection)
                    return res
                return dclass.get_db_prep_value(
                    self,
                    value,
                    connection,
                    prepared
                )

            def get_db_prep_save(self, value, connection):
                if(GET_DEFAULT_FROM_DB == value or (None == value and not (self.null))):
                    res = DbFieldDecorator.get_default_from_db(self, connection)
                    return res
                return dclass.get_db_prep_save(
                    self,
                    value,
                    connection
                )

            def validate(self, value, model_instance):
                res =  dclass.validate(self, value, model_instance)
                dbname = model_instance.__class__._default_manager.db
                self.__has_mm_values = False
                if('default' != dbname):
                    con = connections[dbname]
                    db_descr = DbFieldDecorator.get_db_descr(self, con, dbname)

                    data_type = Undefined
                    is_unsigned = 0
                    if(None != db_descr):
                        data_type = db_descr.get('data_type')
                        is_unsigned = db_descr.get('is_unsigned')
                        numeric_precision = db_descr.get('numeric_precision')
                        numeric_scale = db_descr.get('numeric_scale')


                    if(data_type in DATA_SIZES_VALIDATE):
                        self.min_value = fbyte_min(data_type, is_unsigned)
                        self.max_value = fbyte_max(data_type, is_unsigned)

                    if(data_type in ('float', 'double', 'real', 'decimal', 'numeric', 'dec', 'fixed')):
                        print "db_descr = ", db_descr
                        self.max_digits = int(numeric_precision)

                        if(numeric_scale != None):
                            self.decimal_places = int(numeric_scale)
                            up_digits = self.max_digits - self.decimal_places

                            if(data_type in ('decimal', 'numeric', 'dec', 'fixed')):
                                self.max_value =        \
                                    10**(up_digits) -   \
                                    decimal.Decimal(0.1**(self.decimal_places + 1))
                                self.min_value =        \
                                    - 10**(up_digits) + \
                                    decimal.Decimal(0.1**(self.decimal_places + 1))
                            else:
                                self.max_value =        \
                                    10**(up_digits) -   \
                                    decimal.Decimal(0.1**(self.decimal_places + 1))
                                self.min_value =        \
                                    - 10**(up_digits) + \
                                    decimal.Decimal(0.1**(self.decimal_places + 1))
                        else:
                            if(data_type in ('decimal', 'numeric', 'dec', 'fixed')):
                                self.decimal_places = 0
                            else:
                                self.decimal_places = self.max_digits
                            up_digits = self.max_digits
                            self.max_value = 10**(up_digits)
                            self.min_value = -10**(up_digits)



                        print "\t\t\t self.min_value = \n", value, self.min_value


                    if(hasattr(self, 'max_value') and self.max_value):
                        self.validators = [validator
                            for validator in self.validators
                                if not isinstance(validator, MaxValueValidator)]
                        self.validators.append(MaxValueValidator(self.max_value))

                    if(hasattr(self, 'min_value') and self.max_value):
                        self.validators = [validator
                            for validator in self.validators
                                if not isinstance(validator, MinValueValidator)]
                        self.validators.append(MinValueValidator(self.min_value))

                return res

        return NewClass

    @classmethod
    def get_default_from_db(cls, self, connection, dbname):

        '''
            Возвращает значение поля по-умолчанию из базы данных.
            Обращения к описанием полей кешируются по числу обращений.
            Количество обращений задается константой
                DEFAULT_FIELDS_TIMEOUT_TIMES
        '''


        default = None
        data_type = None
        if (not (self.null)):
            default = 0

        ## Если значение по умолчанию не определено,
        ## то запрашиваем его в базе данных.


        db_descr = cls.get_db_descr(self, connection, dbname)

        if(None != db_descr):
            default  = db_descr.get('column_default')
            data_type = db_descr.get('data_type')


        #if("bannerpriority" == self.name):
            #print
            #print "default = ", default, data_type
            #print

        if (self.null and None == default ):
            default = None;
        else:

            if('int' == data_type):
                default = toint(default, 0)
            elif('smallint' == data_type):
                default = toint(default, 0)
            elif('tinyint' == data_type):
                default = toint(default, 0)


            elif('bigint' == data_type):
                default = toint(default, 0)
            elif('float' == data_type):
                default = tofloat(default, 0.0)
            elif('double' == data_type):
                default = tofloat(default, 0.0)
            elif('decimal' == data_type):
                default = tofloat(default, 0.0)
            elif('timestamp' == data_type):
                try:
                    default = datetime.datetime.strptime(
                        default,
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    if (self.null):
                        default = None
                    else:
                        default = 0
            else:
                pass
                #logging.warn(u'unknown data_type %s'%(data_type))


        if("reservedtime" == self.name):
            print
            print "default 2 = ", default, data_type
            print



        if(self.default == GET_DEFAULT_FROM_DB):
            self.default = default
            self.value = default

        return default



    @classmethod
    def get_db_descr(cls, self, connection, dbname):

        ## Добавляем словарь с типами данных из базы
        if(not hasattr(self.model, 'default_fields_data_types_from_db')):
            self.model.default_fields_data_types_from_db = {}

        ## Добавляем словарь с числом обращений.
        if(not hasattr(self.model, 'default_fields_times')):
            self.model.default_fields_times = {}

        ## Достаем из словаря количество обращений к полю.
        ## Если в словаре ничего нет, то считаем, нуль обращений.
        self.model.default_fields_times[self.db_column] = \
            self.model.default_fields_times.get(
                self.db_column, 0
            )
        ## Если число обращений больше некоторой константы обнуляем это число.
        ## Значение по умолчанию в этом случае считаем неопределенным.
        ## Иначе увеличиваем число обращений.
        if(DEFAULT_FIELDS_TIMEOUT_TIMES == self.model.default_fields_times[self.db_column]):
            self.model.default_fields_times[self.db_column] = 0
            db_descr = {}
        else:
            self.model.default_fields_times[self.db_column] += 1;
            db_descr = self.model.default_fields_data_types_from_db.get(self.db_column, {})


        if({} == db_descr):
            c = connection.cursor()
            try:
                ##
                ## Хитрая работа с cast( DEFAULT( %s ) as char(256) )
                ##  связана с тем, что без привидения может быть возвращен
                ##  не тот объект, который описан в базе,
                ##  а его представление в python.
                ##  Это не всегда оказывается приемлемым.
                ## Например, дата 0000-00-00 00:00:00 распознается как None.
                ## И при вставке в базу вставляется как NULL.
                ##
                #c.execute("SELECT cast( DEFAULT( `%s` ) as char(256) ) FROM `%s` LIMIT 1;"%(
                    #self.db_column,
                    #self.model._meta.db_table
                #))

                c.execute(
                    "select "
                        "LOCATE('unsigned', COLUMN_TYPE) > 0 as is_unsigned,"
                        "numeric_precision,"
                        "numeric_scale,"
                        "column_default,"
                        "data_type,"
                        "column_name "
                    "from "
                        "information_schema.columns "
                    "where "
                        "table_schema = '%s' "
                        "and table_name = '%s' "
                        "and column_name = '%s';"
                    %(
                    dbname,
                    self.model._meta.db_table,
                    self.db_column,
                ))

                #fdescr = c.fetchone()
                db_descr = fetchoneDict(c)

            finally:
                c.close()


        if(None != db_descr):
            self.model.default_fields_data_types_from_db[self.db_column] = db_descr

        return db_descr
