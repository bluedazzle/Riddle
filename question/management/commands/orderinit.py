# coding=utf-8
from __future__ import unicode_literals

import pandas as pd

from django.core.management.base import BaseCommand

from question.models import Question


class Command(BaseCommand):
    def order_init(self, execl, questions=0):
        model_question = Question
        df = pd.read_excel(execl, sheet_name=u'order', encoding='utf-8')
        infos = df.ix[:, [u'title', u'order_id', u'question_type', u'difficult', u'right_answer', u'wrong_answer', u'resource_url', u'new_order_id']]
        questions_list = []
        model_question.objects.all().delete()

        if questions == 0:
            lines = len(infos[u'title'])
        else:
            lines = questions
        for line in range(lines):
            print('初始化题目' + str(line))
            questions_list.append((infos[u'title'][line], int(infos[u'order_id'][line]), infos[u'question_type'][line], int(infos[u'difficult'][line]),
                                   infos[u'right_answer'][line], infos[u'wrong_answer'][line], infos[u'resource_url'][line], int(infos[u'new_order_id'][line])))
        questions_list.sort(key=lambda x: (x[7]))

        for num in range(len(questions_list)):
            obj_question = model_question(title=questions_list[num][0], order_id=questions_list[num][7],
                                          question_type=questions_list[num][2], difficult=questions_list[num][3],
                                          right_answer_id=1, right_answer=questions_list[num][4],
                                          wrong_answer_id=2, wrong_answer=questions_list[num][5],
                                          resource_url=questions_list[num][6])
            obj_question.save()


    def handle(self, *args, **options):
        self.order_init(u'question/management/commands/order.xlsx', 1230)