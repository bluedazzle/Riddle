from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import HttpResponse
from core.dss.Mixin import MultipleJsonResponseMixin, CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin

from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode

class Test(View, StatusWrapMixin, JsonResponseMixin, CheckTokenMixin):
    def get(self, request, *args, **kwargs):
        return self.render_to_response({})