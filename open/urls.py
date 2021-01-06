# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from open.views import *

urlpatterns = [
    url(r'^test/$', Test.as_view()),
]
