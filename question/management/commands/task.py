# coding=utf-8
from __future__ import unicode_literals

import pandas as pd
from urllib import parse
import pypinyin
import requests
import random

prefix = 'http://cai-ta.ecdn.plutus-cat.com/assets/'

def pingyin(word):
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s += ''.join(i)
    return s


def song_init(execl, songs=0):
    df = pd.read_excel(execl, sheet_name=u'songs', encoding='utf-8')
    infos = df.ix[:, [u'歌手名', u'歌曲名']]
    if songs == 0:
        lines = len(infos[u'歌手名'])
    else:
        lines = songs
    for line in range(lines):
        url = prefix + pingyin(infos[u'歌手名'][line]) + '_' + pingyin(infos[u'歌曲名'][line]) + '.m4a'
        print(url)



def question_init(execl, questions=0):
    df = pd.read_excel(execl, sheet_name=u'questions', encoding='utf-8')
    infos = df.ix[:, [u'id', u'题目顺序', u'题目类型', u'正确答案', u'错误答案']]
    questions_list = []
    name_dic = {}
    if questions == 0:
        lines = len(infos[u'id'])
    else:
        lines = questions
    for line in range(lines):
        pics_list = []
        pics_num = 0
        try_num = 0
        try_total = 0
        if pd.isna(infos[u'id'][line]) or pd.isna(infos[u'题目顺序'][line]) or pd.isna(infos[u'题目类型'][line]) \
                or pd.isna(infos[u'正确答案'][line]) or pd.isna(infos[u'错误答案'][line]):
            continue
        if not name_dic.get(infos[u'正确答案'][line]):
            name_dic[infos[u'正确答案'][line]] = 1

        while pics_num < 3:
            pic = infos[u'正确答案'][line] + '/' + infos[u'正确答案'][line] + '-' + str(name_dic[infos[u'正确答案'][line]]) + '.jpg'
            encode_pic = parse.quote(pic)
            url = prefix + encode_pic
            try_total = try_total + 1
            if try_total == 20:
                break
            try:
                resp = requests.get(str(url), timeout=4)
            except :
                try_num = try_num + 1
                name_dic[infos[u'正确答案'][line]] = name_dic[infos[u'正确答案'][line]] + 1
                if try_num >= 3:
                    try_num = 0
                    name_dic[infos[u'正确答案'][line]] = 0
                continue
            if resp.status_code != 200:
                try_num = try_num + 1
                name_dic[infos[u'正确答案'][line]] = name_dic[infos[u'正确答案'][line]] + 1
                if try_num >= 3:
                    try_num = 0
                    name_dic[infos[u'正确答案'][line]] = 0
                continue
            try_num = 0
            name_dic[infos[u'正确答案'][line]] = name_dic[infos[u'正确答案'][line]] + 1
            pics_num = pics_num + 1
            pics_list.append(url)
        if pics_num < 3:
            continue
        print(pics_list)
        questions_list.append((infos[u'id'][line], infos[u'题目顺序'][line], infos[u'题目类型'][line],
                               infos[u'正确答案'][line], infos[u'错误答案'][line], pics_list))

    questions_list.sort(key=lambda x: (x[1]))
    print("total: " + str(len(questions_list)))
    print(questions_list)

def table_init(execl, people=0):
    df = pd.read_excel(execl, sheet_name=u'people', encoding='utf-8')
    infos = df.ix[:, [u'名称', u'数量', u'国籍']]
    people_map = {u'欧美': u'日韩', u'日韩': u'华人', u'华人': u'欧美'}
    people_list = {}
    question_list = []
    if people == 0:
        lines = len(infos[u'名称'])
    else:
        lines = people
    for line in range(lines):
        if not people_list.get(infos[u'国籍'][line]):
            people_list[infos[u'国籍'][line]] = []
        people_list[infos[u'国籍'][line]].append(infos[u'名称'][line])

    for line in range(lines):
        question_num = round(int(infos[u'数量'][line]) / 3)
        for num in range(question_num):
            wrong_answer = random.sample(people_list[people_map[infos[u'国籍'][line]]], 1)[0]
            tag = ''.join(
                random.sample('1234567890ZYXWVUTSRQPONMLKJIHGFEDCBAZYXWVUTSRQPONMLKJIHGFEDCBA', 8)).replace(" ", "")
            question_list.append((tag, infos[u'名称'][line], wrong_answer, infos[u'国籍'][line]))

    question_list.sort(key=lambda x: (x[0]))
    print(question_list)

    table = {u'题目顺序':[], u'id':[], u'题目类型':[], u'正确答案':[], u'错误答案':[], u'国籍':[]}
    for num in range(len(question_list)):
        table[u'题目顺序'].append(num+1)
        table[u'id'].append(num+1)
        table[u'题目类型'].append(1)
        table[u'正确答案'].append(question_list[num][1])
        table[u'错误答案'].append(question_list[num][2])
        table[u'国籍'].append(question_list[num][3])

    table_excel = pd.DataFrame(table)
    table_excel.to_excel('auto_questions.xlsx', sheet_name='questions')


if __name__ == "__main__":
    # question_init(u'auto_questions.xlsx', 10)
    table_init(u'pics.xlsx')
