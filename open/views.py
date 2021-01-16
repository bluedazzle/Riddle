from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import HttpResponse
from core.dss.Mixin import MultipleJsonResponseMixin, CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin
from question.models import Question

from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode
import json
import requests

from prometheus_client import Counter, Histogram

# 第三个列表定义参数 inc 用来加一
c = Counter('my_requests_total_test_total', 'test', ['method', 'endpoint'])

class Test(View, JsonResponseMixin):
    def get(self, request, *args, **kwargs):
        c.labels('get', '/').inc()
        c.labels('post', '/submit').inc()
        return self.render_to_response()
