# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from account.views import *

urlpatterns = [
    url(r'^info/$', UserInfoView.as_view()),
    url(r'^register/$', UserRegisterView.as_view()),
    url(r'^wx_login/$', WxLoginView.as_view()),
    url(r'^captcha/$', VerifyCodeView.as_view()),
    url(r'^captcha/validate/$', ValidateVerifyView.as_view()),
    url(r'^share/$', UserShareView.as_view()),
    url(r'^invite_code/$', InviteKeyView.as_view()),
    url(r'^invite_bonus/$', InviteBonusView.as_view()),
    url(r'^valid/$', ValidView.as_view()),
    url(r'^device_info/$', DeviceInfoView.as_view()),
    url(r'^test/$', TEST.as_view())
]
