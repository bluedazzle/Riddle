# coding: utf-8
import requests
import json

from django.db.models import Q
from django.utils import timezone

from account.models import User
from core.consts import EVENT_TRANSFORM_ACTIVATE, EVENT_TRANSFORM_REGISTER, EVENT_TRANSFORM_PAY, EVENT_TRANSFORM_TWICE
from event.models import ClickEvent, TransformEvent


def transform_type_to_str(type: int):
    if type == EVENT_TRANSFORM_ACTIVATE:
        return 'ACTIVATE_APP'
    elif type == EVENT_TRANSFORM_REGISTER:
        return 'REGISTER'
    elif type == EVENT_TRANSFORM_PAY:
        return 'PURCHASE'
    elif type == EVENT_TRANSFORM_TWICE:
        return 'START_APP'
    else:
        return ''


def transform_blank_to_zero(user: User):
    if user.android_id == '':
        android_id = '0'
    else:
        android_id = user.android_id
    if user.imei == '':
        imei = '0'
    else:
        imei = user.imei
    if user.oaid == '':
        oaid = '0'
    else:
        oaid = user.oaid
    if user.mac == '':
        mac = '0'
    else:
        mac = user.mac
    return android_id, imei, oaid, mac


def handle_transform_event(event: ClickEvent, type):
    if event.company == 'kuaishou':
        time = timezone.localtime().microsecond
        if type == EVENT_TRANSFORM_PAY:
            pay_amount = 1
        else:
            pay_amount = 0
        url = '{0}&event_type={1}&event_time={2}&purchase_amount={3}'. \
            format(event.callback, type + 1, time, pay_amount)
        # print(url)
        try:
            resp = requests.get(url, timeout=5)
            json_data = resp.json()
            if json_data.get('result') == 1:
                return
            raise ValueError('kuaishou transform callback failed')
        except Exception as e:
            raise e
    if event.company == 'tencent':
        url = '{0}'.format(event.callback)
        headers = {
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        action_type = transform_type_to_str(type)
        data = {'actions': [{
            'user_id': {
                'hash_imei': event.imei,
                'hash_android_id': event.android_id,
                'oaid': event.oaid
            },
            'action_type': action_type,
            'action_param': {
                'length_of_stay': 1
            }
        }]}
        # print(url)
        try:
            # res = requests.Request('POST', url, headers=headers, data=json.dumps(data))
            # print(res.prepare().method, res.prepare().url, res.prepare().headers, res.prepare().body)
            res = requests.post(url, headers=headers, data=json.dumps(data), timeout=5).content
            json_data = json.loads(res)
            if json_data.get('code') == 0:
                return
            raise ValueError('tencent transform callback failed')
        except Exception as e:
            raise e
    else:
        signature = 'wRZHhuS-UsgJh-KNr-mGHpYgoJjXKSXWE'
        url = '{0}&imei={1}&oaid={2}&event_type={3}&signature={4}'. \
            format(event.callback, event.imei, event.oaid, type, signature)
        # print(url)
        try:
            resp = requests.get(url, timeout=5)
            json_data = resp.json()
            if json_data.get('code') == 0:
                return
            raise ValueError(json_data.get('msg'))
        except Exception as e:
            raise e


def handle_activate_event(user: User):
    model = TransformEvent
    record = model.objects.filter(user_id=user.id, action='activate').all()
    if record.exists():
        return

    android_id, imei, oaid, mac = transform_blank_to_zero(user)
    objs = ClickEvent.objects.filter(Q(android_id=android_id) | Q(imei=imei)
                                     | Q(oaid=oaid) | Q(mac=mac)).all()
    # if user.imei == '':
    #     return
    # objs = ClickEvent.objects.filter(imei=user.imei).all()
    if not objs:
        return
    if objs[0].channel != 'default' and objs[0].channel != user.channel:
        return
    obj = model(transform=objs[0].company, channel=objs[0].channel, action='activate', user_id=user.id, name=user.name)
    obj.save()
    handle_transform_event(objs[0], EVENT_TRANSFORM_ACTIVATE)
    obj = model(transform=objs[0].company, channel=objs[0].channel, action='register', user_id=user.id, name=user.name)
    obj.save()
    handle_transform_event(objs[0], EVENT_TRANSFORM_REGISTER)
    return


def handle_pay_event(user: User):
    model = TransformEvent
    android_id, imei, oaid, mac = transform_blank_to_zero(user)
    objs = ClickEvent.objects.filter(Q(android_id=android_id) | Q(imei=imei)
                                     | Q(oaid=oaid) | Q(mac=mac)).all()
    # if user.imei == '':
    #     return
    # objs = ClickEvent.objects.filter(imei=user.imei).all()
    if not objs:
        return
    if objs[0].channel != 'default' and objs[0].channel != user.channel:
        return
    obj = model(transform=objs[0].company, channel=objs[0].channel, action='pay', user_id=user.id, name=user.name)
    obj.save()
    handle_transform_event(objs[0], EVENT_TRANSFORM_PAY)
    return


def handle_twice_event(user: User):
    model = TransformEvent
    android_id, imei, oaid, mac = transform_blank_to_zero(user)
    objs = ClickEvent.objects.filter(Q(android_id=android_id) | Q(imei=imei)
                                     | Q(oaid=oaid) | Q(mac=mac)).all()
    # if user.imei == '':
    #     return
    # objs = ClickEvent.objects.filter(imei=user.imei).all()
    if not objs:
        return
    if objs[0].channel != 'default' and objs[0].channel != user.channel:
        return
    obj = model(transform=objs[0].company, channel=objs[0].channel, action='twice', user_id=user.id, name=user.name)
    obj.save()
    handle_transform_event(objs[0], EVENT_TRANSFORM_TWICE)
    return
