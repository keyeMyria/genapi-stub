 # -*- coding: utf-8 -*-


class InsertReplaceMixin(object):

    def save(self, *args, **kwargs):
        return_id = self.replace()
        if(return_id):
            self.pk = return_id
        
