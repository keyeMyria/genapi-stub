 # -*- coding: utf-8 -*-

import six

from .common import Common

class WrongBaseno(Exception):
    '''
        Возможно, имеет смысл вынести отдельно,
    '''
    detail = 'wrong baseno'

class Sharded(Common):

    @property
    def sharded_databases(self):
        return self.__class__.objects.sharded_databases

    @property
    def baseno(self):
        for index, name in six.iteritems(self.sharded_databases):
            if name == self.db:
                return index
        return None

    @baseno.setter
    def baseno(self, index):
        database = self.sharded_databases.get(index)
        if not database:
            raise WrongBaseno('wrong baseno')
        self.db = database;

    @property
    def db(self):
        return self._state.db

    @db.setter
    def db(self, value):
        self._state.db = value;

    @classmethod
    def get_dynamic_model(cls, *args, **kwargs):
        if(hasattr(cls.objects, 'get_dynamic_model')):
            index = kwargs.pop('index', None)
            baseno = kwargs.pop('baseno', None)
            database = kwargs.pop('database ', None)

            return cls.objects.get_dynamic_model(
                index = index,
                baseno = baseno,
                database = database
            )
        return None

    @classmethod
    def get_dynamic_object(cls, *args, **kwargs):
        index = kwargs.pop('index', None)
        baseno = kwargs.pop('baseno', None)
        database = kwargs.pop('database ', None)


        model = cls.get_dynamic_model(
            cls,
            index = index,
            baseno = baseno,
            database = database
        )

        if(not model):
            return None

        fkwargs = {}
        for key, val in six.iteritems(kwargs):
            if (key in cls._meta.get_all_field_names()):
                fkwargs[key] = val


        obj = model(*args, **fkwargs)
        ### TODO:   WTF???
        obj._state.db = model.db
        obj._state.adding = False
        return obj



    class Meta:
        abstract = True


