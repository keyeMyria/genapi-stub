 # -*- coding: utf-8 -*-


class InsertIgnoreMixin(object):

    def save(self, *args, **kwargs):
        self.insert_ignore()
