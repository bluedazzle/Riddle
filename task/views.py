# coding: utf-8
import json
import logging
import datetime

from django.db import transaction
from django.shortcuts import render

# Create your views here.
from django.views.generic import DetailView, View
from redis.lock import Lock
from baseconf.models import TaskConf
from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode
from core.cache import get_daily_task_config_from_cache, set_daily_task_config_to_cache, \
    get_common_task_config_from_cache, set_common_task_config_to_cache, search_task_id_by_cache, \
    set_task_id_to_cache, client_redis_riddle
from core.consts import TASK_OK, TASK_DOING, TASK_TYPE_DAILY, TASK_TYPE_COMMON, TASK_FINISH, DEFAULT_LOCK_TIMEOUT, \
    SIGN_WATCH_AD_COUNT
from core.dss.Mixin import CheckTokenMixin, JsonResponseMixin
from task.models import DailyTask, CommonTask
from account.models import UserSingerCount
from task.utils import create_task, create_task_history, send_reward, get_singer_id


class DailyTaskListView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, DetailView):
    task_config = None
    model = TaskConf

    def get_daily_task_config(self):
        conf = get_daily_task_config_from_cache()
        if not conf:
            obj = self.model.objects.all()[0]
            conf = obj.daily_task_config
            set_daily_task_config_to_cache(conf)
            conf = json.loads(conf)
        self.task_config = conf

    @staticmethod
    def format_target(target):
        if isinstance(target, bool):
            return 1 if target else 0
        return target

    def get(self, request, *args, **kwargs):
        self.get_daily_task_config()
        daily_task_list = []
        task_ok = 0
        stk = self.user.daily_sign_in_token
        for task in self.task_config:
            target = self.format_target(getattr(self.user, task.get("target")))
            title = task.get("title")
            for itm in task.get("detail"):
                task = create_task(self.user, target, task.get("slug"), title, **itm)
                if task.get("status") == TASK_OK:
                    task_ok += 1
                daily_task_list.append(task)
        daily_task_list.sort(key=lambda x: x.get("status"))
        if stk != self.user.daily_sign_in_token:
            # 更新 sign_token 时保存 user
            self.user.save()
        return self.render_to_response({"daily_task": daily_task_list, 'task_ok_count': task_ok})


class CommonTaskListView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, DetailView):
    task_config = None
    model = TaskConf

    def get_common_task_config(self):
        conf = get_common_task_config_from_cache()
        if not conf:
            obj = self.model.objects.all()[0]
            conf = obj.common_task_config
            set_common_task_config_to_cache(conf)
            conf = json.loads(conf)
        self.task_config = conf

    @staticmethod
    def format_target(target):
        if isinstance(target, bool):
            return 1 if target else 0
        return target

    def get(self, request, *args, **kwargs):
        self.get_common_task_config()
        common_task_list = list()
        task_ok = 0

        for task in self.task_config:
            target = self.format_target(getattr(self.user, task.get("target")))
            title = task.get("title")
            for itm in task.get("detail"):
                task = create_task(self.user, target, task.get("slug"), title, **itm)
                if task.get("status") == TASK_OK:
                    task_ok += 1
                common_task_list.append(task)
        common_task_list.sort(key=lambda x: x.get("status"))
        return self.render_to_response({"common_task": common_task_list, 'task_ok_count': task_ok})


class TaskListView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, DetailView):
    model = TaskConf

    @staticmethod
    def get_common_task_config():
        conf = get_common_task_config_from_cache()
        if not conf:
            obj = TaskConf.objects.all()[0]
            conf = obj.common_task_config
            set_common_task_config_to_cache(conf)
            conf = json.loads(conf)
        return conf

    @staticmethod
    def get_daily_task_config():
        conf = get_daily_task_config_from_cache()
        if not conf:
            obj = TaskConf.objects.all()[0]
            conf = obj.daily_task_config
            set_daily_task_config_to_cache(conf)
            conf = json.loads(conf)
        return conf

    @staticmethod
    def format_target(target):
        if isinstance(target, bool):
            return 1 if target else 0
        return target

    def get(self, request, *args, **kwargs):
        common_task_config = self.get_common_task_config()
        daily_task_config = self.get_daily_task_config()

        user_singer_count_list = UserSingerCount.objects.filter(user_id=self.user.id).order_by('singer_id').all()

        if not user_singer_count_list.exists():
            user_singer_count_list = []
            for i in range(3):
                user_singer_count_list.append(UserSingerCount(user_id=self.user.id, singer_id=i))

            UserSingerCount.objects.bulk_create(user_singer_count_list)

        daily_task = list()

        for task_conf in daily_task_config:
            target = self.format_target(getattr(self.user, task_conf.get("target")))
            title = task_conf.get("title")
            daily_continue_count_stage = self.user.daily_continue_count_stage

            if task_conf.get("slug") == "DAILY_CONTINUE_COUNT":
                if daily_continue_count_stage >= len(task_conf.get("detail")):
                    daily_continue_count_stage = len(task_conf.get("detail")) - 1

                for i in range(daily_continue_count_stage, len(task_conf.get("detail"))):
                    task = create_task(self.user, target, task_conf.get("slug"), title,
                                       **task_conf.get("detail")[i])
                    task["stage"] = i

                    if task["status"] == TASK_FINISH:
                        task["current_level"] = task["level"]

                    daily_task.append(task)
            else:
                for itm in task_conf.get("detail"):
                    task = create_task(self.user, target, task_conf.get("slug"), title, **itm)
                    daily_task.append(task)

        singer_task = list()
        common_task = list()

        for task_conf in common_task_config:
            title = task_conf.get("title")

            if task_conf.get("slug") == "COMMON_TASK_SINGER_GUSS_RIGHT":
                for user_singer_count in user_singer_count_list:
                    target = user_singer_count.right_count
                    singer_id = user_singer_count.singer_id

                    if singer_id >= len(task_conf["detail"]):
                        continue

                    task = create_task(self.user, target, task_conf.get("slug"), title,
                                       **task_conf["detail"][singer_id])

                    singer_task.append(task)
            elif task_conf.get("slug") == "COMMON_TASK_SIGN":
                pass
            else:
                target = self.format_target(getattr(self.user, task_conf.get("target")))

                for itm in task_conf.get("detail"):
                    task = create_task(self.user, target, task_conf.get("slug"), title, **itm)
                    if task.get("status") == TASK_OK:
                        pass
                    common_task.append(task)

        return self.render_to_response({"daily_task": daily_task, "singer_task": singer_task,
                                        "common_task": common_task,
                                        "daily_reward_amount": self.user.daily_reward_amount})


class FinishTaskView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, View):
    task_type = TASK_TYPE_DAILY
    task_lock = None

    def valid_task(self, slug, task_id):
        if search_task_id_by_cache(task_id):
            self.update_status(StatusCode.ERROR_TASK_FINISHED)
            raise ValueError()
        if self.task_type == TASK_TYPE_DAILY:
            objs = DailyTask.objects.filter(task_id=task_id).all()
        else:
            objs = CommonTask.objects.filter(task_id=task_id).all()
        if objs.exists():
            self.update_status(StatusCode.ERROR_TASK_FINISHED)
            raise ValueError()
        return True

    def get_task_type(self, slug):
        task_type_dict = {'DAILY': TASK_TYPE_DAILY, 'COMMON': TASK_TYPE_COMMON}
        task_type = slug.split('_')[0]
        task_type = task_type.upper()
        self.task_type = task_type_dict.get(task_type, TASK_TYPE_DAILY)

    def get_task_config(self):
        def get_common_task_config():
            conf = get_common_task_config_from_cache()
            if not conf:
                obj = TaskConf.objects.all()[0]
                conf = obj.common_task_config
                set_common_task_config_to_cache(conf)
                conf = json.loads(conf)
            return conf

        def get_daily_task_config():
            conf = get_daily_task_config_from_cache()
            if not conf:
                obj = TaskConf.objects.all()[0]
                conf = obj.daily_task_config
                set_daily_task_config_to_cache(conf)
                conf = json.loads(conf)
            return conf

        config_dict = {TASK_TYPE_DAILY: get_daily_task_config, TASK_TYPE_COMMON: get_common_task_config}
        conf_func = config_dict.get(self.task_type, get_daily_task_config)
        conf = conf_func()
        return conf

    def get_task_dict(self):
        task_dict = {}
        conf = self.get_task_config()
        for task in conf:
            title = task.get("title")

            if task.get("slug") == "DAILY_CONTINUE_COUNT":
                task = create_task(self.user, 0, task.get("slug"), title, **task.get("detail")[self.user.daily_continue_count_stage])
                task_dict[task.get('id')] = task
            else:
                for itm in task.get("detail"):
                    task = create_task(self.user, 0, task.get("slug"), title, **itm)
                    task_dict[task.get('id')] = task
        return task_dict

    def send_reward(self, slug, task_id):
        task_dict = self.get_task_dict()
        task = task_dict.get(task_id)

        if not task:
            self.update_status(StatusCode.ERROR_TASK_NOT_EXIST)
            raise ValueError('任务不存在')

        if slug == "COMMON_TASK_SINGER_GUSS_RIGHT":
            singer = task.get('singer')
            singer_id = get_singer_id(singer)

            objs = UserSingerCount.objects.filter(user_id=self.user.id, singer_id=singer_id)

            if not objs.exists():
                raise ValueError('任务未完成')

            user_singer = objs[0]
            user_singer_count = user_singer.right_count

            if user_singer_count < task.get('level'):
                raise ValueError('任务未完成')

            max_singer_id = UserSingerCount.objects.filter(user_id=self.user.id).order_by('-singer_id')[0].singer_id
            if max_singer_id < 10:
                user_singer.right_count = 0
                user_singer.singer_id = max_singer_id + 1
                user_singer.save()
        elif slug == "DAILY_CONTINUE_COUNT":
            if self.user.continue_count < task.get('level'):
                raise ValueError('任务未完成')
            self.user.continue_count = 0
            self.user.daily_continue_count_stage += 1
        elif slug == "DAILY_SIGN":
            if self.user.daily_sign_in_token < task.get('level'):
                raise ValueError('任务未完成')

            if task.get('level') == 90:
                self.user.daily_sign_in = 0
                self.user.daily_sign_in_token = str(int(self.user.daily_sign_in_token.split("_")[0] + 1)) \
                                                + self.user.daily_sign_in_token.split("_")[1]

        reward = task.get('reward')
        reward_type = task.get('reward_type')
        user = send_reward(self.user, reward, reward_type)

        user.save()
        return reward, reward_type

    def create_task_history(self, task_id, slug, **kwargs):
        history = create_task_history(task_id, self.user.id, slug, self.task_type, **kwargs)
        history.save()
        if self.task_type == TASK_TYPE_DAILY:
            set_task_id_to_cache(task_id, 3600 * 24)
        else:
            set_task_id_to_cache(task_id)
        return history

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        self.task_lock = Lock(client_redis_riddle, str(self.user.id) + "valid", DEFAULT_LOCK_TIMEOUT)
        if self.task_lock.locked():
            self.update_status(StatusCode.ERROR_TASK_CLICK)
            return self.render_to_response()
        self.task_lock.acquire()

        try:
            task_id = request.POST.get("task_id")
            slug = request.POST.get('slug')

            if (slug == "COMMON_TASK_SINGER_GUSS_RIGHT" or slug == "DAILY_CONTINUE_COUNT") and \
                    (self.user.wx_open_id == '' or not self.user.wx_open_id):
                self.update_status(StatusCode.ERROR_TASK_WITHDRAW)
                return self.render_to_response(extra={'error': '请绑定微信后提现'})

            self.get_task_type(slug)
            self.valid_task(slug, task_id)
            amount, reward_type = self.send_reward(slug, task_id)
            self.create_task_history(task_id, slug)
            self.task_lock.release()
            return self.render_to_response(
                {"coin": self.user.coin, "cash": self.user.cash, 'amount': amount, 'reward_type': reward_type})
        except ValueError as e:
            logging.exception(e)
            self.task_lock.release()
            return self.render_to_response(extra={'error': str(e)})
        except Exception as e:
            logging.exception(e)
            self.update_status(StatusCode.ERROR_DATA)
            self.task_lock.release()
            return self.render_to_response(extra={'error': str(e)})


class DailySignTaskView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, DetailView):
    @staticmethod
    def get_common_task_config():
        conf = get_common_task_config_from_cache()
        if not conf:
            obj = TaskConf.objects.all()[0]
            conf = obj.common_task_config
            set_common_task_config_to_cache(conf)
            conf = json.loads(conf)
        return conf

    def get_last_sign_day(self):
        if len(self.user.daily_sign_in_token.split("_")) == 1:
            self.user.daily_sign_in = 0
            self.user.daily_sign_in_token = str(1) + str(datetime.date.today() - datetime.timedelta(days=1))
            self.user.save()
            return str(datetime.date.today() - datetime.timedelta(days=1))
        return str(self.user.daily_sign_in_token.split("_")[1])

    def get(self, request, *args, **kwargs):
        daily_task_config = self.get_common_task_config()
        daily_task = list()

        last_sign_day = self.get_last_sign_day()
        daily_sign_status = str(datetime.date.today()) == last_sign_day and 1 or 0

        for task_conf in daily_task_config:
            if task_conf.get("slug") == "COMMON_TASK_SIGN":
                target = self.user.daily_sign_in
                title = task_conf.get("title")

                for itm in task_conf.get("detail"):
                    task = create_task(self.user, target, task_conf.get("slug"), title, **itm)
                    daily_task.append(task)

        return self.render_to_response({"daily_sign_in": self.user.daily_sign_in, "daily_task": daily_task,
                                        "daily_sign_status": daily_sign_status})


class DailySignView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, View):
    sign_lock = None

    def get(self, request, *args, **kwargs):
        self.sign_lock = Lock(client_redis_riddle, str(self.user.id) + "valid", DEFAULT_LOCK_TIMEOUT)
        if self.sign_lock.locked():
            self.update_status(StatusCode.ERROR_TASK_CLICK)
            return self.render_to_response()
        self.sign_lock.acquire()

        if self.user.daily_watch_ad < SIGN_WATCH_AD_COUNT:
            self.update_status(StatusCode.ERROR_DATA)

            self.sign_lock.release()
            return self.render_to_response()

        if len(self.user.daily_sign_in_token.split("_")) == 1:
            self.user.daily_sign_in = 1
            self.user.daily_sign_in_token = str(1) + str(datetime.date.today())
            self.user.save()

            self.sign_lock.release()
            return self.render_to_response()

        if self.user.daily_sign_in_token.split("_")[1] == str(datetime.date.today()):
            self.update_status(StatusCode.ERROR_TASK_FINISHED)

            self.sign_lock.release()
            return self.render_to_response()

        self.user.daily_sign_in += 1
        self.user.daily_sign_in_token = self.user.daily_sign_in_token.split("_")[0] + str(datetime.date.today())
        self.user.save()

        self.sign_lock.release()
        return self.render_to_response()
