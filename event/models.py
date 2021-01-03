# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from account.models import BaseModel


class AdEvent(ExportModelOperationsMixin("AdEvent"), BaseModel):
    ad_type = models.CharField(max_length=128)
    channel = models.CharField(default='PANGLE', max_length=100)
    extra = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.IntegerField(default=0)
    app_id = models.CharField(max_length=128)

    def __unicode__(self):
        return '{0}-{1}'.format(self.user_id, self.ad_type)


class ObjectEvent(ExportModelOperationsMixin("ObjectEvent"), BaseModel):
    object = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    extra = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.IntegerField(default=0)
    app_id = models.CharField(max_length=128)

    def __unicode__(self):
        return '{0}-{1}'.format(self.user_id, self.object)
