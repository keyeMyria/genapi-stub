 # -*- coding: utf-8 -*-

import sys
import django.db.models

from apps.genapi.utils.log.logmeta import LogMeta
from apps.genapi.utils.log.logmeta import LogModelMeta

from django.utils.six import with_metaclass

from django.db import models

import apps.genapi.caching.base

import copy
import sys
from functools import update_wrapper
from django.utils.six.moves import zip

import django.db.models.manager  # Imported to register signal handler.
from django.conf import settings
from django.core.exceptions import (ObjectDoesNotExist,
    MultipleObjectsReturned, FieldError, ValidationError, NON_FIELD_ERRORS)
from django.db.models.fields import AutoField, FieldDoesNotExist
from django.db import (router, transaction, DatabaseError, DEFAULT_DB_ALIAS)
from django.db.models.query import Q
from django.db.models.query_utils import DeferredAttribute, deferred_class_factory
from django.db.models.deletion import Collector
from django.db.models.options import Options
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry
from django.utils.encoding import force_str, force_text
from django.utils import six
from django.utils.text import get_text_list, capfirst


from .manager import Manager


from caching.base import CachingMixin, NO_CACHE

import inspect
import copy
from django.forms.models import model_to_dict

from apps.genapi.utils import combimethod


class Common(CachingMixin, django.db.models.Model):

    _pkcacher = None

    objects = Manager(caching_timeout = NO_CACHE)

    class Meta:
        abstract = True

    isfictive  = False

    def __init__(self, *args, **kwargs):
        super(Common, self).__init__(*args, **kwargs)
        self.initial_copy = copy.deepcopy(self)
        self.initial_copy.initial_copy = copy.deepcopy(self.initial_copy)

    def to_dict(self):
        model = self.__class__
        attribute_dict = {
            prop : getattr(self,prop)
                for prop in self.__dict__.copy()
                    if not prop.startswith('_')
        }
        return attribute_dict

    def _to_nonfield_dict(self,exclude_methods=True):
        base_attr_list = dir(type('dummy', (object,), {}))
        this_attr_list = dir(self)
        this_attr_set = set(this_attr_list)
        base_attr_set = set(base_attr_list)
        this_attr_set.difference_update(base_attr_set)
        attribute_list = [
            attr
            for attr in this_attr_set
                if hasattr(self, attr)
                    and (not attr.startswith('_'))
                    and (not callable(getattr(self,attr)))
        ]
        attribute_dict = {}
        for attribute in attribute_list:
            value = getattr(self, attribute)
            attribute_dict.update({attribute: copy.copy(value)})
        return attribute_dict


    def _to_dict(self):
        return model_to_dict(self)



    @combimethod
    def insert(self, *args, **kwargs):
        return self.__class__.objects.insert([self], *args, **kwargs)

    @insert.classmethod
    def insert(cls, *args, **kwargs):
        return cls.objects.insert(*args, **kwargs)

    @combimethod
    def replace(self, *args, **kwargs):
        return self.__class__.objects.replace([self], *args, **kwargs)

    @replace.classmethod
    def replace(cls, *args, **kwargs):
        return cls.objects.replace(*args, **kwargs)

    @combimethod
    def insert_update(self, *args, **kwargs):
        return self.__class__.objects.insert_update([self], *args, **kwargs)

    @insert_update.classmethod
    def insert_update(cls, *args, **kwargs):
        return cls.objects.insert_update(*args, **kwargs)

    @combimethod
    def insert_ignore(self, *args, **kwargs):
        return self.__class__.objects.insert_ignore([self], *args, **kwargs)

    @insert_ignore.classmethod
    def insert_ignore(cls, *args, **kwargs):
        return cls.objects.insert_ignore(*args, **kwargs)


    @classmethod
    def fictive(cls, *args, **kwargs):
        obj = cls(pk = 0, *args, **kwargs)
        obj.isfictive = True
        return obj


    @classmethod
    def dict(cls, attr = 'pk', **kwargs):
        if isinstance(attr, str):
            return {
                getattr(obj, attr) : obj
                for obj in cls.objects.filter(**kwargs)
            }
        if isinstance(attr, tuple):
            return {
                tuple([getattr(obj, a) for a in attr]) : obj
                for obj in cls.objects.filter(**kwargs)
            }

    @classmethod
    def list(cls, **kwargs):
        return [
            obj
            for obj in cls.objects.filter(**kwargs)
        ]

    def get_or_create(self, queryset = None, **kwargs):

        if(not queryset):
            queryset = self.__class__.objects.all()

        return queryset.get_or_create(
            **kwargs
        )


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Saves the current instance. Override this in a subclass if you want to
        control the saving process.

        The 'force_insert' and 'force_update' parameters can be used to insist
        that the "save" must be an SQL insert or update (or equivalent for
        non-SQL backends), respectively. Normally, they should not be set.
        """

        using = using or router.db_for_write(self.__class__, instance=self)
        if force_insert and (force_update or update_fields):
            raise ValueError("Cannot force both insert and updating in model saving.")

        if update_fields is not None:
            # If update_fields is empty, skip the save. We do also check for
            # no-op saves later on for inheritance cases. This bailout is
            # still needed for skipping signal sending.
            if len(update_fields) == 0:
                return

            update_fields = frozenset(update_fields)
            field_names = set()

            for field in self._meta.fields:
                if not field.primary_key:
                    field_names.add(field.name)

                    if field.name != field.attname:
                        field_names.add(field.attname)

            non_model_fields = update_fields.difference(field_names)

            if non_model_fields:
                raise ValueError("The following fields do not exist in this "
                                 "model or are m2m fields: %s"
                                 % ', '.join(non_model_fields))

        # If saving to the same database, and this model is deferred, then
        # automatically do a "update_fields" save on the loaded fields.
        elif not force_insert and self._deferred and using == self._state.db:
            field_names = set()
            for field in self._meta.concrete_fields:
                if not field.primary_key and not hasattr(field, 'through'):
                    field_names.add(field.attname)
            deferred_fields = [
                f.attname for f in self._meta.fields
                if (f.attname not in self.__dict__ and
                    isinstance(self.__class__.__dict__[f.attname], DeferredAttribute))
            ]

            loaded_fields = field_names.difference(deferred_fields)
            if loaded_fields:
                update_fields = frozenset(loaded_fields)

        self.save_base(using=using, force_insert=force_insert,
                       force_update=force_update, update_fields=update_fields)
    save.alters_data = True

    def save_base(self, raw=False, force_insert=False,
                  force_update=False, using=None, update_fields=None):
        """
        Handles the parts of saving which should be done only once per save,
        yet need to be done in raw saves, too. This includes some sanity
        checks and signal sending.

        The 'raw' argument is telling save_base not to save any parent
        models and not to do any changes to the values before save. This
        is used by fixture loading.
        """
        using = using or router.db_for_write(self.__class__, instance=self)
        assert not (force_insert and (force_update or update_fields))
        assert update_fields is None or len(update_fields) > 0
        cls = origin = self.__class__
        # Skip proxies, but keep the origin as the proxy model.
        if cls._meta.proxy:
            cls = cls._meta.concrete_model
        meta = cls._meta
        if not meta.auto_created:
            signals.pre_save.send(sender=origin, instance=self, raw=raw, using=using,
                                  update_fields=update_fields)
        with transaction.commit_on_success_unless_managed(using=using, savepoint=False):
            if not raw:
                self._save_parents(cls, using, update_fields)
            updated = self._save_table(raw, cls, force_insert, force_update, using, update_fields)
        # Store the database on which the object was saved
        self._state.db = using
        # Once saved, this is no longer a to-be-added instance.
        self._state.adding = False

        # Signal that the save is complete
        if not meta.auto_created:
            signals.post_save.send(sender=origin, instance=self, created=(not updated),
                                   update_fields=update_fields, raw=raw, using=using)

    save_base.alters_data = True

    def _save_parents(self, cls, using, update_fields):
        """
        Saves all the parents of cls using values from self.
        """
        meta = cls._meta
        for parent, field in meta.parents.items():
            # Make sure the link fields are synced between parent and self.
            if (field and getattr(self, parent._meta.pk.attname) is None
                    and getattr(self, field.attname) is not None):
                setattr(self, parent._meta.pk.attname, getattr(self, field.attname))
            self._save_parents(cls=parent, using=using, update_fields=update_fields)
            self._save_table(cls=parent, using=using, update_fields=update_fields)
            # Set the parent's PK value to self.
            if field:
                setattr(self, field.attname, self._get_pk_val(parent._meta))
                # Since we didn't have an instance of the parent handy set
                # attname directly, bypassing the descriptor. Invalidate
                # the related object cache, in case it's been accidentally
                # populated. A fresh instance will be re-built from the
                # database if necessary.
                cache_name = field.get_cache_name()
                if hasattr(self, cache_name):
                    delattr(self, cache_name)


    def x_get_pk_val(self, meta):
        return self._get_pk_val(meta)

    def _save_table(self, raw=False, cls=None, force_insert=False,
                    force_update=False, using=None, update_fields=None):
        """
        Does the heavy-lifting involved in saving. Updates or inserts the data
        for a single table.
        """
        meta = cls._meta
        non_pks = [f for f in meta.local_concrete_fields if not f.primary_key]

        if update_fields:
            non_pks = [f for f in non_pks
                       if f.name in update_fields or f.attname in update_fields]

        pk_val = self.x_get_pk_val(meta)
        pk_set = pk_val is not None

        if not pk_set and (force_update or update_fields):
            raise ValueError("Cannot force an update in save() with no primary key.")
        updated = False
        # If possible, try an UPDATE. If that doesn't update anything, do an INSERT.
        if pk_set and not force_insert:
            base_qs = cls._base_manager.using(using)
            values = [(f, None, (getattr(self, f.attname) if raw else f.pre_save(self, False)))
                      for f in non_pks]
            forced_update = update_fields or force_update
            updated = self._do_update(base_qs, using, pk_val, values, update_fields,
                                      forced_update)
            if force_update and not updated:
                raise DatabaseError("Forced update did not affect any rows.")
            if update_fields and not updated:
                raise DatabaseError("Save with update_fields did not affect any rows.")
        if not updated:
            if meta.order_with_respect_to:
                # If this is a model with an order_with_respect_to
                # autopopulate the _order field
                field = meta.order_with_respect_to
                order_value = cls._base_manager.using(using).filter(
                    **{field.name: getattr(self, field.attname)}).count()
                self._order = order_value

            fields = meta.local_concrete_fields

            if not pk_set:
                fields = [f for f in fields if not isinstance(f, AutoField)]

            update_pk = bool(meta.has_auto_field and not pk_set)

            result = self._do_insert(cls._base_manager, using, fields, update_pk, raw)
            if update_pk:
                setattr(self, meta.pk.attname, result)
        return updated

    def x_do_update_base_qs(self, base_qs, pk):
        return base_qs.filter(pk=pk)

    def _do_update(self, base_qs, using, pk_val, values, update_fields, fupdate):
        """
        This method will try to update the model. If the model was updated (in
        the sense that an update query was done and a matching row was found
        from the DB) the method will return True.
        """
        if not values:
            # We can end up here when saving a model in inheritance chain where
            # update_fields doesn't target any field in current model. In that
            # case we just say the update succeeded. Another case ending up here
            # is a model with just PK - in that case check that the PK still
            # exists.
            return update_fields is not None or base_qs.filter(pk=pk_val).exists()
        else:
            return base_qs.filter(pk=pk_val)._update(values) > 0


    def _do_insert(self, manager, using, fields, update_pk, raw):
        """
        Do an INSERT. If update_pk is defined then this method should return
        the new pk for the model.
        """


        return manager._insert([self], fields=fields, return_id=update_pk,
                               using=using, raw=raw)



