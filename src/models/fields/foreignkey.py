# -*- coding: utf-8 -*-

from django.db import models


class ForeignKey(models.ForeignKey):

    def get_attname(self):
        return '%sid' % self.name[3:]
