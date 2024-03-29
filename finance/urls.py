# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from finance.views import *

urlpatterns = [
    url(r'^cash_records/$', CashRecordListView.as_view()),
    url(r'^cash/$', CreateCashRecordView.as_view()),
    url(r'^exchange_records/$', ExchangeRecordListView.as_view()),
    url(r'^exchange/$', CreateExchangeRecordView.as_view()),
    url(r'^reward/$', RewardView.as_view()),
    url(r'^rewards/$', RewardListView.as_view()),
    url(r'^lucky_draw/$', LuckyDrawView.as_view()),
    url(r'^game_cash/$', GameCashView.as_view()),
    url(r'^game_video/$', GameVideoView.as_view()),
]
