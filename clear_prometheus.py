# coding: utf-8
# 用于清楚导致数据库迁徙报错的脚本

import os
import re


def replace(file):
    with open(file, 'r', encoding='utf-8') as f:
        w_str = ""
        for line in f.readlines():
            if re.search(r'bases=\(django_prometheus.models.Mixin, models.Model\),', line):
                line = ''
                w_str += line
            else:
                w_str += line
    with open(file, 'w', encoding='utf-8') as f:
        f.write(w_str)


def get_file_list(dir):
    for home, dirs, files in os.walk(dir):
        if home.endswith("migrations"):
            print(home)
            for filename in files:
                file = os.path.join(home, filename)
                replace(file)


if __name__ == "__main__":
    get_file_list(os.getcwd())
