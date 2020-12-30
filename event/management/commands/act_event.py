# coding=utf-8
from __future__ import unicode_literals

import datetime

from django.core.management.base import BaseCommand

from account.models import User
from event.utils import upload_activate_event

class Command(BaseCommand):
    def event_init(self):
        users = User.objects.filter(create_time__gte=datetime.datetime.now().date()).all()
        print(len(users))
        for user in users:
            upload_activate_event(user)

    def handle(self, *args, **options):
        self.event_init()