from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import HttpResponse
from core.dss.Mixin import MultipleJsonResponseMixin, CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin
from question.models import Question

from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode
import json
import requests


class Test(View, JsonResponseMixin):
    def get(self, request, *args, **kwargs):
        for i in range(100):
            a = i + 1
            que = Question()
            que.title = '第{0}题'.format(a)
            que.order_id = a
            que.type = 1
            que.right_answer_id = 1
            que.wrong_answer_id = 2
            que.right_answer = 'xxx'
            que.wrong_answer = 'aaa'
            que.resource_url = 'aaa.xxx'
            que.save()

        return self.render_to_response()
