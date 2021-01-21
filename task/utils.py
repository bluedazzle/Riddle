# coding: utf-8
import hashlib
import json

import datetime
import random
import uuid

from django.db.models import BooleanField
from django.utils import timezone


from account.models import User
from core.consts import STATUS_USED,STATUS_FAIL, STATUS_REVIEW, STATUS_FINISH
from core.cache import search_task_id_by_cache, set_task_id_to_cache
from core.consts import TASK_DOING, TASK_OK, TASK_FINISH, TASK_TYPE_DAILY, TASK_TYPE_COMMON
from task.models import DailyTask, CommonTask
from finance.models import CashRecord
from core.wx import send_money_by_open_id

def valid_task(slug, task_id):
    if search_task_id_by_cache(task_id):
        return True
    if slug.startswith('DAILY_'):
        objs = DailyTask.objects.filter(task_id=task_id).all()
    else:
        objs = CommonTask.objects.filter(task_id=task_id).all()
    if objs.exists():
        if slug.startswith('DAILY_'):
            set_task_id_to_cache(task_id, 3600 * 24)
        else:
            set_task_id_to_cache(task_id)
        return True
    return False


def create_task(user: User, target, task_slug: str, title_template, *args, **kwargs):
    task_slug = task_slug.upper()
    task = {'current_level': target}
    task.update(kwargs)
    if task_slug == 'COMMON_TASK_SIGN':
        daily_sign_stage = user.daily_sign_in_token.split("_")[0]
        unique_str = ','.join([str(user.id), task_slug, str(kwargs.get("level")),
                               str(kwargs.get("reward")), daily_sign_stage])
    elif task_slug.startswith('DAILY_'):
        date = datetime.date.today()
        unique_str = ','.join([str(user.id), task_slug, str(kwargs.get("level")), str(kwargs.get("reward")), str(date)])
    elif task_slug == "COMMON_TASK_SINGER_GUSS_RIGHT":
        unique_str = ','.join([str(user.id), task_slug, str(kwargs.get("level")), str(kwargs.get("reward")),
                               str(kwargs.get("singer"))])
    else:
        unique_str = ','.join([str(user.id), task_slug, str(kwargs.get("level")), str(kwargs.get("reward"))])
    task_id = hashlib.md5(unique_str.encode(encoding='UTF-8')).hexdigest()
    task['id'] = task_id

    if task_slug == 'COMMON_TASK_SINGER_GUSS_RIGHT':
        task['title'] = title_template.format(kwargs.get("level"), kwargs.get("singer"))
    else:
        task['title'] = title_template.format(kwargs.get("level"))

    task['slug'] = task_slug
    task['reward'] = kwargs.get("reward")
    task['reward_type'] = kwargs.get("reward_type")
    status = TASK_DOING

    if target >= kwargs.get("level"):
        status = TASK_OK
    if valid_task(task_slug, task_id):
        status = TASK_FINISH
    task['status'] = status
    return task


def create_task_history(task_id, user_id, slug, task_type=TASK_TYPE_DAILY, **kwargs):
    model_dict = {TASK_TYPE_DAILY: DailyTask, TASK_TYPE_COMMON: CommonTask}
    model = model_dict.get(task_type, DailyTask)
    new_history = model()
    detail = json.dumps(kwargs)
    new_history.task_id = task_id
    new_history.belong_id = user_id
    new_history.slug = slug
    new_history.detail = detail
    return new_history


def draw(user: User, cash):
    if user.wx_open_id == '' or not user.wx_open_id:
        raise ValueError('绑定微信后提现')

    uid = str(uuid.uuid1())
    suid = ''.join(uid.split('-'))

    cash_record = CashRecord()
    cash_record.cash_type = '任务提现'
    cash_record.belong = user
    cash_record.status = STATUS_REVIEW
    cash_record.reason = '审核中'
    cash_record.trade_no = suid
    cash_record.cash = cash
    resp = send_money_by_open_id(suid, user.wx_open_id, cash)

    if resp.get('result_code') == 'SUCCESS':
        cash_record.reason = '成功'
        cash_record.status = STATUS_FINISH
    else:
        fail_message = resp.get('err_code_des', 'default_error')
        cash_record.reason = fail_message
        cash_record.status = STATUS_FAIL

    cash_record.save()


def send_reward(user: User, amount: int, reward_type: str):
    reward_type = reward_type.upper()

    if reward_type == 'WITHDRAW':
        draw(user, amount)
        user.daily_reward_amount -= amount

        return user

    reward_type_dict = {'COIN': 'coin', 'CASH': 'cash'}
    reward_type_attr = reward_type_dict.get(reward_type)
    if not reward_type_attr:
        raise ValueError('奖励类型不存在')
    old_value = getattr(user, reward_type_attr)
    new_value = old_value + amount
    setattr(user, reward_type_attr, new_value)
    return user


def daily_task_attr_reset(user: User):
    now_time = timezone.localtime()
    if not user.new_withdraw and user.current_level <= 5:
        user.daily_reward_stage = 5
        user.check_point_draw = True
    if user.daily_reward_modify.astimezone().day != now_time.day:
        user.daily_reward_expire = None
        user.daily_reward_draw = False
        user.daily_reward_stage = 20
        user.daily_reward_count = 0
        user.daily_right_count = 0
        user.continue_count = 0
        user.daily_continue_count_stage = 0
        user.daily_reward_amount = 2000
        user.daily_watch_ad = 0
        user.daily_reward_modify = now_time
        user.daily_coin_exchange = False
        user.daily_lucky_draw = False
        user.daily_withdraw = False
        if user.daily_sign_in == 7:
            user.daily_sign_in = 0
            user.daily_sign_in_token = create_token()
        user.daily_sign_in += 1
    if user.daily_reward_expire:
        if now_time > user.daily_reward_expire:
            user.daily_reward_draw = False
    return user


def update_task_attr(user: User, attr: str):
    old_value = getattr(user, attr)
    new_value = None
    if isinstance(old_value, int):
        new_value = old_value + 1
    if isinstance(old_value, bool):
        new_value = True
    if new_value:
        setattr(user, attr, new_value)
    return user


def create_token(count=32):
    count = 62 if count > 62 else count
    token = ''.join(
        random.sample('ZYXWVUTSRQPONMLKJIHGFEDCBA1234567890zyxwvutsrqponmlkjihgfedcbazyxwvutsrqponmlkjihgfedcba',
                      count)).replace(" ", "")
    return token


def get_singer_id(singer):
    singer_list = {
        "邓丽君": 0,
        "周华健": 1,
        "李宗盛": 2,
        "蒋大为": 3,
        "宋祖英": 4,
        "刘德华": 5,
        "毛阿敏": 6,
        "那英": 7,
        "刘若英": 8,
        "韩磊": 9,
        "汪峰": 10,
    }

    return singer_list.get(singer, -1)
