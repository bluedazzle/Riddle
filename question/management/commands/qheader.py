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

    def qheader_init(self, execl, qheader=0):
        model_question = Question
        df = pd.read_excel(execl, sheet_name=u'qheader', encoding='utf-8')
        infos = df.ix[:, [u'题目顺序', u'正确答案', u'错误答案', u'图片1', u'图片2', u'图片3']]
        if qheader == 0:
            lines = len(infos[u'名称'])
        else:
            lines = qheader
        for line in range(lines):
            num = 3
            index_list = []
            index_list.append(infos[u'图片1'][line])
            index_list.append(infos[u'图片2'][line])
            index_list.append(infos[u'图片3'][line])
            qheader_list = []
            for index in index_list:
                pic = infos[u'正确答案'][line] + '/' + infos[u'正确答案'][line] + '-' + str(int(index)) + '.webp'
                encode_pic = parse.quote(pic)
                url = prefix + encode_pic
                print(url)
                try:
                    resp = requests.get(str(url), timeout=4)
                except:
                    continue
                if resp.status_code != 200:
                    continue
                qheader_list.append(url)

            if len(qheader_list) == num:
                print(line, infos[u'正确答案'][line], qheader_list)
                obj_qheads = model_question.objects.filter(order_id=int(infos[u'题目顺序'][line])).all()
                if not obj_qheads:
                    continue
                obj_qhead = obj_qheads[0]
                obj_qhead.right_answer = infos[u'正确答案'][line]
                obj_qhead.wrong_answer = infos[u'错误答案'][line]
                obj_qhead.resources = json.dumps(qheader_list)
                obj_qhead.save()


    def handle(self, *args, **options):
        self.qheader_init(u'question/management/commands/qheader.xlsx', 20)
