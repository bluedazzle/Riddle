# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from django.views.generic import CreateView
from django.views.generic import DetailView

from core.Mixin.JsonRequestMixin import JsonRequestMixin
from core.Mixin.StatusWrapMixin import StatusWrapMixin
from core.dss.Mixin import CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin
from event.forms import AdEventForm
from event.models import ClickEvent


class CreateAdEventView(CheckTokenMixin, StatusWrapMixin, JsonRequestMixin, FormJsonResponseMixin, CreateView):
    form_class = AdEventForm
    http_method_names = ['post']
    conf = {}

    def form_valid(self, form):
        try:
            super(CreateAdEventView, self).form_valid(form)
            event = form.save()
            event.user_id = self.user.id
            event.app_id = self.app.app_id
            event.save()
            return self.render_to_response(dict())
        except Exception as e:
            return self.render_to_response(extra={'error': e.message})


class ClickEventView(StatusWrapMixin, JsonResponseMixin, DetailView):
    model = ClickEvent

    def get(self, request, *args, **kwargs):
        company = request.GET.get('company', 'default')
        channel = request.GET.get('channel', 'default')
        aid = request.GET.get('aid', 'aid')
        aid_name = request.GET.get('aid_name', 'aid_name')
        callback = request.GET.get('callback', 'callback')
        android_id = request.GET.get('android_id', 'android_id')
        if android_id == 'android_id':
            android_id = request.GET.get('hash_android_id', 'android_id')
        imei = request.GET.get('imei', 'imei')
        if imei == 'imei':
            imei = request.GET.get('muid', 'imei')
        oaid = request.GET.get('oaid', 'oaid')
        mac = request.GET.get('mac', 'mac')
        if callback == 'callback' and imei == 'imei' and oaid == 'oaid':
            return self.render_to_response()
        obj = self.model(company=company, channel=channel, aid=aid, aid_name=aid_name, callback=callback,
                         android_id=android_id, imei=imei, oaid=oaid, mac=mac)
        obj.save()
        return self.render_to_response()