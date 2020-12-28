# coding: utf-8
import requests

from django.db.models import Q

from account.models import User
from core.consts import EVENT_TRANSFORM_ACTIVATE, EVENT_TRANSFORM_PAY, EVENT_TRANSFORM_TWICE
from event.models import ClickEvent, TransformEvent

def handle_transform_event(callback, imei, oaid, type):
    # print(callback, imei, oaid, type)
    signature = 'wRZHhuS-UsgJh-KNr-mGHpYgoJjXKSXWE'
    url = 'https://ad.oceanengine.com/track/activate/?callback={0}&imei={1}&oaid={2}&event_type={3}&signature={4}'.\
        format(callback, imei, oaid, type, signature)
    try:
        resp = requests.get(url, timeout=3)
        json_data = resp.json()
        # print json_data
        if json_data.get('code') == 0:
            return
        raise ValueError(json_data.get('msg'))
    except Exception as e:
        raise e


def handle_activate_event(user: User):
    model = TransformEvent
    objs = ClickEvent.objects.filter(Q(android_id=user.android_id) | Q(imei=user.imei)
                                     | Q(oaid=user.oaid) | Q(mac=user.mac)).all()
    if not objs:
        return
    object = model(transform='bytedance', action='activate', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_ACTIVATE)
    return

def handle_pay_event(user: User):
    model = TransformEvent
    objs = ClickEvent.objects.filter(Q(android_id=user.android_id) | Q(imei=user.imei)
                                      | Q(oaid=user.oaid) | Q(mac=user.mac)).all()
    if not objs:
        return
    object = model(transform='bytedance', action='pay', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_PAY)
    return

def handle_twice_event(user: User):
    model = TransformEvent
    objs = ClickEvent.objects.filter(Q(android_id=user.android_id) | Q(imei=user.imei)
                                      | Q(oaid=user.oaid) | Q(mac=user.mac)).all()
    if not objs:
        return
    object = model(transform='bytedance', action='twice', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_TWICE)
    return