# coding: utf-8

from __future__ import unicode_literals
from __future__ import absolute_import

import json
from django.core.paginator import EmptyPage

from account.models import User
from open.models import App
from core.Mixin.StatusWrapMixin import StatusCode
from .Serializer import serializer
from .TimeFormatFactory import TimeFormatFactory
from core.cache import client_redis_riddle

try:
    from django.http import HttpResponse
except ImportError:
    raise RuntimeError('django is required in django simple serializer')


class RespCacheMixin(object):
    def render_to_response(self, context={}, **response_kwargs):
        context_dict = self.context_serialize(context)
        json_context = self.json_serializer(context_dict)
        path = self.request.path
        site = self.site.slug
        key = '{0}_{1}'.format(path, site)
        if not client_redis_riddle.get(key):
            client_redis_riddle.setex(key, json_context, 30)
        return HttpResponse(json_context, content_type='application/json', **response_kwargs)

    def get(self, request, *args, **kwargs):
        path = self.request.path
        site = self.site.slug
        key = '{0}_{1}'.format(path, site)
        cache_data = client_redis_riddle.get(key)
        if cache_data:
            return HttpResponse(cache_data, content_type='application/json')
        return super(RespCacheMixin, self).get(request, *args, **kwargs)


class CheckTokenMixin(object):
    token = None
    user = None
    app = None
    force_check = True

    def get_current_token(self):
        self.token = self.request.GET.get('token', None) or self.request.POST.get('token', None)
        if not self.token:
            self.token = self.request.session.get(
                'token', '')
        return self.token

    def check_token(self):
        # 废弃
        self.get_current_token()
        user_list = User.objects.filter(token=self.token)
        if user_list.exists():
            self.user = user_list[0]
            return True
        return False

    def check_user(self, request):
        user = getattr(request, 'account')
        if user:
            self.user = user
        return user

    def wrap_check_token_result(self):
        if not self.user:
            if self.force_check:
                self.update_status(StatusCode.ERROR_PERMISSION_DENIED)
            return False
        return True

    def wrap_check_app_result(self):
        if not self.app:
            self.update_status(StatusCode.ERROR_API_PERMISSION_DENIED)
            return False
        return True

    def check_app(self):
        access_token = self.request.GET.get('access_token', None) or self.request.POST.get('access_token', None)
        app_list = App.objects.filter(access_token=access_token).all()
        if app_list.exists():
            self.app = app_list[0]
            return True
        return False

    def dispatch(self, request, *args, **kwargs):
        self.check_user(request)
        self.check_app()
        if not self.wrap_check_app_result():
            return self.render_to_response()
        if not self.wrap_check_token_result() and self.force_check:
            return self.render_to_response()
        return super(CheckTokenMixin, self).dispatch(request, *args, **kwargs)


class JsonResponseMixin(object):
    datetime_type = 'timestamp'
    foreign = False
    many = False
    include_attr = []
    exclude_attr = []

    def time_format(self, time_obj):
        time_func = TimeFormatFactory.get_time_func(self.datetime_type)
        return time_func(time_obj)

    def context_serialize(self, context, *args, **kwargs):
        try:
            context.pop('view')
            context.pop('object')
        except KeyError:
            pass
        except AttributeError:
            pass
        # if kwargs.get('multi_extend'):
        #     self.include_attr.extend(kwargs.get('multi_extend'))
        return serializer(data=context,
                          datetime_format=self.datetime_type,
                          output_type='raw',
                          foreign=self.foreign,
                          many=self.many,
                          include_attr=self.include_attr,
                          exclude_attr=self.exclude_attr,
                          dict_check=True)

    @staticmethod
    def json_serializer(context):
        return json.dumps(context, indent=4)

    def render_to_response(self, context={}, **response_kwargs):
        context_dict = self.context_serialize(context)
        json_context = self.json_serializer(context_dict)
        return HttpResponse(json_context, content_type='application/json', **response_kwargs)


class FormJsonResponseMixin(JsonResponseMixin):
    def context_serialize(self, context, *args, **kwargs):
        form_list = []
        form = context.get('form', None)
        if form:
            for itm in form.fields:
                f_dict = {'field': str(itm)}
                form_list.append(f_dict)
        context_dict = super(FormJsonResponseMixin, self).context_serialize(context, *args, **kwargs)
        context_dict['form'] = form_list
        return context_dict

    def get_success_url(self):
        return None

    def form_invalid(self, form):
        super(FormJsonResponseMixin, self).form_invalid(form)
        self.update_status(StatusCode.ERROR_FORM)
        return self.render_to_response(dict(), extra=form.errors)


class MultipleJsonResponseMixin(JsonResponseMixin):
    def context_serialize(self, context, *args, **kwargs):
        # multi_extend = [i for i in context.keys() if not i.startswith('object') and i.endswith('_list')]
        # kwargs['multi_extend'] = multi_extend
        page_dict = {}
        is_paginated = context.get('is_paginated', None)
        if is_paginated:
            page_obj = context['page_obj']
            page_dict['current'] = page_obj.number
            page_dict['total'] = page_obj.paginator.num_pages
            try:
                previous_page = page_obj.previous_page_number()
            except EmptyPage:
                previous_page = None
            try:
                next_page = page_obj.next_page_number()
            except EmptyPage:
                next_page = None
            page_dict['previous'] = previous_page
            page_dict['next'] = next_page
            page_dict['page_range'] = [{'page': i} for i in page_obj.paginator.page_range]
        try:
            context.pop('paginator')
            context.pop('object_list')
        except KeyError:
            pass
        except AttributeError:
            pass
        context_dict = super(MultipleJsonResponseMixin, self).context_serialize(context, *args, **kwargs)
        context_dict['page_obj'] = page_dict
        return context_dict
