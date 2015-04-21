 # -*- coding: utf-8 -*-

import re
import six

from caching.base import CachingManager, CachingMixin


def modify_model_for_table_sharding(
    model,
    chtname,
    parent,
    database
):
    xdb_table = chtname(model._meta.db_table)

    ## Словарь атрибутов модели запроса,
    ## которые не являются полями модели Django.
    xfields = {
        name: value
        for name, value in six.iteritems(vars(model))
            if (
                (not name.startswith('_'))
                or (name == "__str__")
                or (name == "__repr__")
                or (name == "__unicode__")
            )
    }

    ## Обновляем словарь атрибутов, полями модели запроса.
    xfields.update({f.name: f for f in model._meta.fields})



    ## Создаем динамическую модель.
    dynamic_model = create_model(
        name = "Dynamic_%s"%(xdb_table),
        parent = parent,
        fields = xfields,
        options = {
            'app_label': model._meta.app_label,
            'db_table' : xdb_table
        }
    )

    if(database):
        dynamic_model.db = database
    ## Заменяем модель запроса
    return dynamic_model

def modify_query_for_table_sharding(
    query,
    chtname,
    parent,
    database
):
    dynamic_model = modify_model_for_table_sharding(
        query.model,
        chtname,
        parent,
        database
    )

    return query

def create_model(
    name,
    parent,
    fields=None,
    app_label='',
    module='',
    options=None,
    admin_opts=None
):
    """
    Создает динамическую модель.
    """
    class Meta:
        ## Использование type('Meta', ...) чревато
        ## возникновением ошибок `dictproxy` во время создания модели.
        pass

    if app_label:
        ## Выставляем `app_label` для модели через `Meta`.
        setattr(Meta, 'app_label', app_label)

    ## Обновляем `Meta` значениями из `options`
    if options is not None:
        for key, value in six.iteritems(options):
            setattr(Meta, key, value)

    ## Словарь атрибутов модели.
    attrs = {}

    ## Заполняем словарь атрибутов.
    if fields:
        attrs.update(fields)

    ## Обновляем словарь атрибутов.
    ## Мы не хотим, чтобы некоторые атрубуты были перезаписаны.
    attrs.update({'__module__': module, 'Meta': Meta})

    ## Создаем класс модели.
    model = type(name, (parent,), attrs)

    ## Создаем класс для админки.
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model
