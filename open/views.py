from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import HttpResponse
from core.dss.Mixin import MultipleJsonResponseMixin, CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin

from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode
import json
import requests


class Test(View, StatusWrapMixin, JsonResponseMixin, CheckTokenMixin):
    @staticmethod
    def utc_s(utc):
        origin_date_str = utc.strip().split('+')[0].split('.')[0].replace('Z', '').split('T')
        d = origin_date_str[0]
        time = origin_date_str[1].split(':')
        h = int(time[0]) + 8
        if h > 24:
            h = h - 24
        m, s = time[1], time[2]
        return '{} {}:{}:{}'.format(d, h, m, s)

    def message_handler(self, message):
        alerts = message["alerts"]
        alert_message = []

        for i in range(len(alerts)):
            alert = alerts[i]
            alert = eval(str(alert))
            status = alert["status"]
            labels = alert["labels"]
            annotations = alert["annotations"]
            start_time = self.utc_s(alert["startsAt"])
            end_time = self.utc_s(alert["endsAt"])
            alert_name = labels["alertname"]
            instance = labels["instance"]
            description = annotations["description"]
            message = "------------------------------" + '\n' \
                      + " 猜歌服务器报警 " + '\n' \
                      + "------------------------------" + '\n' \
                      + "状态: " + status + '\n' \
                      + "报警名称: " + alert_name + '\n' \
                      + "报警实例: " + instance + '\n' \
                      + "报警描述: " + description + '\n' \
                      + "开始时间: " + start_time + '\n' \
                      + "结束时间: " + end_time + '\n' \
                      + "------------------------------"
            alert_message.append(message)
        return alert_message

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        alert_messages = self.message_handler(json_data)

        url = "https://open.feishu.cn/open-apis/bot/v2/hook/83e3b754-38cb-4b6a-ac18-55ac62e1fbcc"

        for message in alert_messages:
            requests.post(url=url, json={"msg_type": "text", "content": {"text": message}})

        return self.render_to_response()
