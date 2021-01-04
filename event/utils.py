# coding: utf-8
import requests

from django.db.models import Q
from django.utils import timezone

from account.models import User
from core.consts import EVENT_TRANSFORM_ACTIVATE, EVENT_TRANSFORM_REGISTER, EVENT_TRANSFORM_PAY, EVENT_TRANSFORM_TWICE
from event.models import ClickEvent, TransformEvent

def transform_blank_to_zero(user: User):
    if user.android_id == '':
        android_id = 'android_id'
    else:
        android_id = user.android_id
    if user.imei == '':
        imei = 'imei'
    else:
        imei = user.imei
    if user.oaid == '':
        oaid = 'oaid'
    else:
        oaid = user.oaid
    if user.mac == '':
        mac = 'mac'
    else:
        mac = user.mac
    return android_id, imei, oaid, mac

def handle_transform_event(company, callback, imei, oaid, type):
    if company == 'kuaishou':
        time = timezone.localtime().microsecond
        if type == EVENT_TRANSFORM_PAY:
            pay_amount = 1
        else:
            pay_amount = 0
        url = '{0}&event_type={1}&event_time={2}&purchase_amount={3}'. \
            format(callback, type, time, pay_amount)
        print(url)
        try:
            resp = requests.get(url, timeout=3)
            json_data = resp.json()
            if json_data.get('result') == 1:
                return
            raise ValueError('kuaishou transform callback failed')
        except Exception as e:
            raise e
    else:
        signature = 'wRZHhuS-UsgJh-KNr-mGHpYgoJjXKSXWE'
        url = '{0}&imei={1}&oaid={2}&event_type={3}&signature={4}'.\
            format(callback, imei, oaid, type, signature)
        # print(url)
        try:
            resp = requests.get(url, timeout=3)
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
    object = model(transform=objs[0].company, channel=objs[0].channel, action='activate', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].company, objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_ACTIVATE)
    object = model(transform=objs[0].company, channel=objs[0].channel, action='register', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].company, objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_REGISTER)
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
    object = model(transform=objs[0].company, channel=objs[0].channel, action='pay', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].company, objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_PAY)
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
    object = model(transform=objs[0].company, channel=objs[0].channel, action='twice', user_id=user.id, name=user.name)
    object.save()
    handle_transform_event(objs[0].company, objs[0].callback, objs[0].imei, objs[0].oaid, EVENT_TRANSFORM_TWICE)
    return