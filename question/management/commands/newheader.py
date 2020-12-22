# coding=utf-8
from __future__ import unicode_literals

import pandas as pd
from urllib import parse
import pypinyin
import requests
import random
import json
import string
import numpy as np
from operator import itemgetter

from django.core.management.base import BaseCommand

from question.models import Girl
from question.models import Question

prefix = 'http://cai-ta.ecdn.plutus-cat.com/assets/'


class Command(BaseCommand):

    def newheader_init(self, execl, newheader=0):
        model_question = Question
        df = pd.read_excel(execl, sheet_name=u'newheader', encoding='utf-8')
        infos = df.ix[:, [u'序号', u'题干', u'正确选项', u'错误选项']]
        if newheader == 0:
            lines = len(infos[u'序号'])
        else:
            lines = newheader
        for line in range(lines):
            print(line, infos[u'题干'][line])
            obj_newheads = model_question.objects.filter(order_id=int(infos[u'序号'][line])).all()
            if not obj_newheads:
                continue
            obj_newhead = obj_newheads[0]
            obj_newhead.title = infos[u'题干'][line]
            obj_newhead.right_answer = infos[u'正确选项'][line]
            obj_newhead.wrong_answer = infos[u'错误选项'][line]
            obj_newhead.save()


    def handle(self, *args, **options):
        self.newheader_init(u'question/management/commands/newheader.xlsx')
