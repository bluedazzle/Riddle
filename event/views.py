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
        company = request.GET.get('company', '0')
        channel = request.GET.get('channel', '0')
        callback = request.GET.get('callback', '0')
        android_id = request.GET.get('android_id', '0')
        imei = request.GET.get('imei', '0')
        oaid = request.GET.get('oaid', '0')
        mac = request.GET.get('mac', '0')
        if callback == '0' and imei == '0' and oaid == '0':
            return self.render_to_response()
        obj = self.model(company=company, channel=channel, callback=callback, android_id=android_id, imei=imei, oaid=oaid, mac=mac)
        obj.save()
        return self.render_to_response()