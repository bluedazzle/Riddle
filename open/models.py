# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from account.models import BaseModel


class App(ExportModelOperationsMixin("App"), BaseModel):
    name = models.CharField(max_length=256, unique=True)
    app_id = models.CharField(max_length=128, unique=True)
    secret = models.CharField(max_length=256, unique=True)
    access_token = models.CharField(max_length=128, unique=True)

    wx_app_id = models.CharField(max_length=64, null=True, blank=True)
    wx_app_secret = models.CharField(max_length=64, null=True, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.name)

    def __str__(self):
        return '{0}'.format(self.name)
