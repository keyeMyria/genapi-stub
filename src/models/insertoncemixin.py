 # -*- coding: utf-8 -*-

import MySQLdb
import warnings
import logging

class InsertOnceMixin(object):

    def save(self, *args, **kwargs):
        logger = logging.getLogger("django.db.backends")
        logger.warn("warnings.filterwarnings('ignore', category = MySQLdb.Database.Warning)")
        warnings.filterwarnings('ignore', category = MySQLdb.Warning)
        return_id = self.insert_update(
            update=[(
                self._meta.pk.name,
                'LAST_INSERT_ID(`%s`)'%(self._meta.pk.db_column)
            )]
        )
        if(return_id):
            self.pk = return_id
        warnings.resetwarnings()
        logger.warn("warnings.resetwarnings()")


