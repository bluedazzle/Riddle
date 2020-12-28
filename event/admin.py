# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from event.models import AdEvent, ObjectEvent, ClickEvent, TransformEvent


class AdEventAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'ad_type', 'channel', 'create_time', 'modify_time', 'extra')
    search_fields = ('user_id', 'ad_type')


class ObjectEventAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'object', 'action', 'create_time', 'modify_time', 'extra')
    search_fields = ('user_id', 'object')

class ClickEventAdmin(admin.ModelAdmin):
    list_display = ('mac', 'android_id', 'callback', 'create_time', 'modify_time', 'imei', 'oaid')
    search_fields = ('mac', 'android_id')

class TransformEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'transform', 'action', 'create_time', 'modify_time', 'extra')
    search_fields = ('name', 'transform')


admin.site.register(AdEvent, AdEventAdmin)
admin.site.register(ObjectEvent, ObjectEventAdmin)
admin.site.register(ClickEvent, ClickEventAdmin)
admin.site.register(TransformEvent, TransformEventAdmin)
