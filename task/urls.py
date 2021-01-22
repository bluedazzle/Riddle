# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from task.views import *

urlpatterns = [
    url(r'^daily/$', DailyTaskListView.as_view()),
    url(r'^common/$', CommonTaskListView.as_view()),
    url(r'^task_list/$', TaskListView.as_view()),
    url(r'^daily_sign_task/$', DailySignTaskView.as_view()),
    url(r'^daily_sign/$', DailySignView.as_view()),
    url(r'^valid/$', FinishTaskView.as_view()),
]
