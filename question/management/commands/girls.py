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
    def pingyin(self, word):
        s = ''
        for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
            s += ''.join(i)
        return s

    def girl_init(self, execl, girls=0):
        model_girl = Girl
        df = pd.read_excel(execl, sheet_name=u'girls', encoding='utf-8')
        infos = df.ix[:, [u'名称', u'国籍', u'数量']]
        model_girl.objects.all().delete()
        if girls == 0:
            lines = len(infos[u'名称'])
        else:
            lines = girls
        for line in range(lines):
            index = 1
            num = infos[u'数量'][line]
            girl_list = []
            while index <= num:
                pic = infos[u'名称'][line] + '/' + infos[u'名称'][line] + '-' + str(index) + '.webp'
                encode_pic = parse.quote(pic)
                url = prefix + encode_pic
                try:
                    resp = requests.get(str(url), timeout=4)
                except:
                    continue
                if resp.status_code != 200:
                    continue
                index = index + 1
                girl_list.append(url)
            print(line, infos[u'名称'][line], infos[u'国籍'][line], len(girl_list))
            obj_girl = model_girl(name=infos[u'名称'][line], type=infos[u'国籍'][line],
                                  resources_num=len(girl_list), resources_url=json.dumps(girl_list))
            obj_girl.save()


    def handle(self, *args, **options):
        self.girl_init(u'question/management/commands/auto_girls.xlsx')
