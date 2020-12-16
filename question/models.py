# coding: utf-8

from __future__ import unicode_literals
from django.db import models
from account.models import BaseModel


# Create your models here.


class Girl(BaseModel):
    name = models.CharField(max_length=100, default='')
    type = models.CharField(max_length=128, default='')
    resources_num = models.IntegerField(default=0)
    resources_url = models.TextField(max_length=51200, default='[]')

    def __unicode__(self):
        return '{0}'.format(self.name, self.type, self.resources_num)

    def __str__(self):
        return '{0}'.format(self.name, self.type, self.resources_num)


class Question(BaseModel):
    title = models.CharField(max_length=100, default='')
    order_id = models.IntegerField(unique=True)
    question_type = models.IntegerField(default=1)
    difficult = models.IntegerField(default=1)
    right_answer_id = models.IntegerField()
    right_answer = models.CharField(max_length=100)
    wrong_answer_id = models.IntegerField()
    wrong_answer = models.CharField(max_length=100)
    resource_url = models.CharField(max_length=256, default='')
    resource_type = models.IntegerField(default=1)
    resources = models.TextField(max_length=1024, default='[]')

    def __unicode__(self):
        return '排序:{0}-{1}:{2}'.format(self.order_id, self.title, self.right_answer)

    def __str__(self):
        return '排序:{0}-{1}:{2}'.format(self.order_id, self.title, self.right_answer)
