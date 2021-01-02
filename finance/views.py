# coding: utf-8
from __future__ import unicode_literals

# Create your views here.
import hashlib
import random
import uuid

import datetime

import logging
from django.core.exceptions import ValidationError
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.db import transaction
from django.utils import timezone
from redis.lock import Lock

from account.models import User
from baseconf.models import WithdrawConf
from core.Mixin.ABTestMixin import ABTestMixin
from core.Mixin.JsonRequestMixin import JsonRequestMixin
from core.Mixin.StatusWrapMixin import StatusWrapMixin, StatusCode
from core.cache import REWARD_KEY, client_redis_riddle
from core.consts import DEFAULT_ALLOW_CASH_COUNT, STATUS_USED, PACKET_TYPE_CASH, PACKET_TYPE_WITHDRAW, \
    DEFAULT_NEW_PACKET, DEFAULT_ALLOW_CASH_RIGHT_COUNT, STATUS_FAIL, STATUS_REVIEW, STATUS_FINISH, \
    DEFAULT_MAX_CASH_LIMIT, STATUS_UNUSE, DEFAULT_LOCK_TIMEOUT
from core.dss.Mixin import MultipleJsonResponseMixin, CheckTokenMixin, FormJsonResponseMixin, JsonResponseMixin
from core.utils import get_global_conf
from core.wx import send_money_by_open_id
from finance.forms import CashRecordForm, ExchangeRecordForm
from finance.models import CashRecord, ExchangeRecord, RedPacket
from task.utils import update_task_attr


class CashRecordListView(CheckTokenMixin, StatusWrapMixin, MultipleJsonResponseMixin, ListView):
    model = CashRecord
    slug_field = 'token'
    paginate_by = 2
    ordering = ('-create_time',)
    datetime_type = 'string'

    def get_list_by_user(self):
        self.queryset = self.model.objects.filter(belong=self.user)

    def get_queryset(self):
        self.get_list_by_user()
        return super(CashRecordListView, self).get_queryset()


class ExchangeRecordListView(CheckTokenMixin, StatusWrapMixin, MultipleJsonResponseMixin, ListView):
    model = ExchangeRecord
    slug_field = 'token'
    paginate_by = 2
    ordering = ('-create_time',)
    datetime_type = 'timestamp'

    def get_list_by_user(self):
        self.queryset = self.model.objects.filter(belong=self.user)

    def get_queryset(self):
        self.get_list_by_user()
        return super(ExchangeRecordListView, self).get_queryset()


class RewardListView(CheckTokenMixin, StatusWrapMixin, MultipleJsonResponseMixin, ListView):
    model = RedPacket
    slug_field = 'token'
    paginate_by = 10
    ordering = ('-create_time',)
    datetime_type = 'timestamp'

    def get_list_by_user(self):
        self.queryset = self.model.objects.filter(belong=self.user, reward_type=PACKET_TYPE_WITHDRAW,
                                                  status=STATUS_UNUSE)

    def get_queryset(self):
        self.get_list_by_user()
        return super(RewardListView, self).get_queryset()


class CreateCashRecordView(CheckTokenMixin, StatusWrapMixin, JsonRequestMixin, FormJsonResponseMixin, CreateView):
    form_class = CashRecordForm
    http_method_names = ['post']
    conf = {}
    withdraw_chance = None
    is_new_withdraw = False
    withdraw_token = ''
    withdraw_lock = None

    def simple_safe(self):
        if not self.user.city and not self.user.province and self.user.wx_open_id:
            c_start = self.user.create_time.replace(second=0, microsecond=0)
            c_end = self.user.create_time.replace(second=59, microsecond=999999)
            objs = User.objects.exclude(wx_open_id='').filter(province='', city='',
                                                              create_time__range=(c_start, c_end)).all()
            count = objs.count()
            if count >= 10:
                return False
        return True

    def valid_withdraw_chance(self, cash):
        now_time = timezone.localtime()
        queryset = RedPacket.objects.filter(belong=self.user, amount=cash, status=STATUS_UNUSE,
                                            reward_type=PACKET_TYPE_WITHDRAW,
                                            expire__gte=now_time).all()
        if queryset.exists():
            self.withdraw_chance = queryset[0]
            chance_str = '{0}{1}{2}{3}'.format(
                self.withdraw_chance.amount, self.withdraw_chance.belong_id, self.withdraw_chance.create_time,
                self.withdraw_chance.expire)
            self.withdraw_token = hashlib.md5(chance_str.encode(encoding='UTF-8')).hexdigest()
            self.withdraw_lock = Lock(client_redis_riddle, self.withdraw_token, DEFAULT_LOCK_TIMEOUT)
            if self.withdraw_lock.locked():
                return False
            if self.withdraw_lock.acquire():
                return True
        return False

    def valid_withdraw(self, cash):
        self.conf = get_global_conf()
        if self.user.cash < cash:
            raise ValidationError("提现金额不足")
        if not self.user.wx_open_id:
            raise ValidationError('请绑定微信后提现')
        conf = get_global_conf()
        allow = int(conf.get('allow_cash_right_number', DEFAULT_ALLOW_CASH_RIGHT_COUNT))
        obj = WithdrawConf.objects.all()[0]
        if cash == obj.new_withdraw_threshold:
            if self.user.current_level < 6:
                raise ValidationError('答题5道即可提现')
            if not self.simple_safe():
                raise ValidationError('请稍后再试')
            if not self.user.new_withdraw:
                self.user.new_withdraw = True
                self.is_new_withdraw = True
                self.valid_withdraw_chance(cash)
                return True
        if cash != obj.withdraw_first_threshold and cash != obj.withdraw_second_threshold and cash != obj.withdraw_third_threshold and cash != obj.new_withdraw_threshold:
            raise ValidationError('非法的提现金额')
        if self.user.cash < obj.new_withdraw_threshold:
            raise ValidationError('提现可用金额不足')
        if self.valid_withdraw_chance(cash):
            return True
        raise ValidationError('无提现机会')
        # if self.user.right_count < allow:
        #         raise ValidationError('''抱歉
        # 您还没有获得提现机会
        # 您可以通过以下方式获得提现机会
        # 1. 通过答题参与抽奖
        # 2. 答对{0}道题
        #
        # 当前已答对{1}道'''.format(self.conf.get('allow_cash_right_number', DEFAULT_ALLOW_CASH_RIGHT_COUNT),
        #                     self.user.right_count))
        #     raise ValidationError('提现')

    @transaction.atomic()
    def form_valid(self, form):
        uid = str(uuid.uuid1())
        suid = ''.join(uid.split('-'))
        cash = form.cleaned_data.get('cash', 0)
        try:
            self.valid_withdraw(cash)
        except Exception as e:
            self.update_status(StatusCode.ERROR_FORM)
            return self.render_to_response(extra={"error": e.message})
        super(CreateCashRecordView, self).form_valid(form)
        cash_record = form.save()
        cash_record.belong = self.user
        cash_record.status = STATUS_REVIEW
        cash_record.reason = '审核中'
        cash_record.trade_no = suid
        if cash == 30:
            resp = send_money_by_open_id(suid, self.user.wx_open_id, cash)
            if resp.get('result_code') == 'SUCCESS':
                self.user.cash -= cash
                cash_record.reason = '成功'
                cash_record.status = STATUS_FINISH
                if self.withdraw_chance:
                    self.withdraw_chance.status = STATUS_USED
            else:
                fail_message = resp.get('err_code_des', 'default_error')
                cash_record.reason = fail_message
                cash_record.status = STATUS_FAIL
                obj = WithdrawConf.objects.all()[0]
                if cash == obj.new_withdraw_threshold and self.is_new_withdraw:
                    self.user.new_withdraw = False
        else:
            if self.withdraw_chance:
                self.withdraw_chance.status = STATUS_USED
        cash_record.save()
        update_task_attr(self.user, 'daily_withdraw')
        self.user.save()
        if self.withdraw_chance:
            self.withdraw_chance.save()
        if self.withdraw_lock:
            self.withdraw_lock.release()
        return self.render_to_response(dict())


class CreateExchangeRecordView(CheckTokenMixin, StatusWrapMixin, JsonRequestMixin, FormJsonResponseMixin, CreateView):
    form_class = ExchangeRecordForm
    http_method_names = ['post']
    conf = {}

    def exchange_cash(self, coin):
        # todo 可能需要分布式锁
        self.conf = get_global_conf()
        coin_cash_proportion = self.conf.get('coin_cash_proportion', 1000)
        current_coin = self.user.coin
        if coin_cash_proportion <= 0:
            self.update_status(StatusCode.ERROR_UNKNOWN)
            raise
        if current_coin < coin:
            self.update_status(StatusCode.ERROR_DATA)
            self.message = '金币不足'
            raise ValidationError('金币不足')
        cash = round(coin / float(coin_cash_proportion) * 100, 0)
        self.user.cash += cash
        self.user.coin -= coin
        self.user.save()
        return cash

    @transaction.atomic()
    def form_valid(self, form):
        try:
            super(CreateExchangeRecordView, self).form_valid(form)
            update_task_attr(self.user, 'daily_coin_exchange')
            cash = self.exchange_cash(form.cleaned_data.get('coin', 0))
            exchange_record = form.save()
            exchange_record.belong = self.user
            exchange_record.cash = cash
            exchange_record.proportion = self.conf.get('coin_cash_proportion', 1000)
            exchange_record.save()
            return self.render_to_response(dict())
        except Exception as e:
            return self.render_to_response({})


class RewardView(CheckTokenMixin, StatusWrapMixin, JsonResponseMixin, CreateView):
    model = RedPacket
    http_method_names = ['post']
    conf = {}

    def get_reward(self):
        reward_list = []
        amount = 0
        if self.user.cash >= DEFAULT_MAX_CASH_LIMIT:
            amount = random.randint(1, 2)
        else:
            amount = random.randint(20, 500)
        rp = RedPacket()
        rp.amount = amount
        rp.status = STATUS_USED
        rp.reward_type = PACKET_TYPE_CASH
        rp.belong = self.user
        rp.save()
        self.user.cash += amount
        self.user.save()
        reward = {'reward_type': PACKET_TYPE_CASH, 'amount': amount, 'hit': True}
        reward_list.append(reward)
        reward1 = random.randint(PACKET_TYPE_CASH, PACKET_TYPE_WITHDRAW)
        reward2 = random.randint(PACKET_TYPE_CASH, PACKET_TYPE_WITHDRAW)
        if reward1 == PACKET_TYPE_CASH:
            reward_list.append({'reward_type': PACKET_TYPE_CASH, 'amount': amount, 'hit': False})
        else:
            reward_list.append({'reward_type': reward1, 'amount': 1, 'hit': False})
        if reward2 == PACKET_TYPE_CASH:
            reward_list.append({'reward_type': PACKET_TYPE_CASH, 'amount': amount, 'hit': False})
        else:
            reward_list.append({'reward_type': reward2, 'amount': 1, 'hit': False})
        return reward_list

    def get_new_reward(self):
        conf = get_global_conf()
        new_packet = int(conf.get('new_red_packet', DEFAULT_NEW_PACKET))
        self.user.cash += new_packet
        self.user.new_red_packet = True
        return True

    def post(self, request, *args, **kwargs):
        new_packet = int(request.POST.get('new_packet', 0))
        if new_packet:
            if self.user.new_red_packet:
                self.update_status(StatusCode.ERROR_REPEAT_NEW_PACKET)
                return self.render_to_response()
            self.get_new_reward()
            self.user.save()
            return self.render_to_response()
        if not client_redis_riddle.delete(REWARD_KEY.format(self.user.id)):
            self.update_status(StatusCode.ERROR_REWARD_DENIED)
            return self.render_to_response()
        reward_list = self.get_reward()
        return self.render_to_response({'reward_list': reward_list})


class LuckyDrawView(CheckTokenMixin, ABTestMixin, StatusWrapMixin, JsonResponseMixin, CreateView):
    model = RedPacket
    http_method_names = ['post']
    conf = {}

    def simple_safe(self):
        if not self.user.city and not self.user.province and self.user.wx_open_id:
            c_start = self.user.create_time.replace(second=0, microsecond=0)
            c_end = self.user.create_time.replace(second=59, microsecond=999999)
            objs = User.objects.exclude(wx_open_id='').filter(province='', city='',
                                                              create_time__range=(c_start, c_end)).all()
            count = objs.count()
            if count >= 10:
                return False
        return True

    def valid_withdraw(self, cash):
        if not self.simple_safe():
            raise ValidationError('请稍后重试')
        # self.conf = get_global_conf()
        if not self.user.wx_open_id:
            raise ValidationError('请绑定微信后提现')
        if cash != 100 and cash != 50:
            raise ValidationError('非法的提现金额')
        if self.user.cash < obj.new_withdraw_threshold:
            raise ValidationError('提现可用金额不足')

    def create_cash_record(self, amount):
        try:
            self.valid_withdraw(amount)
            uid = str(uuid.uuid1())
            suid = ''.join(uid.split('-'))
            cash = amount
            cash_record = CashRecord()
            cash_record.cash = cash
            cash_record.cash_type = '抽奖提现'
            cash_record.belong = self.user
            cash_record.status = STATUS_REVIEW
            cash_record.reason = '审核中'
            cash_record.trade_no = suid
            resp = send_money_by_open_id(suid, self.user.wx_open_id, cash)
            if resp.get('result_code') == 'SUCCESS':
                self.user.cash -= cash
                cash_record.reason = '成功'
                cash_record.status = STATUS_FINISH
            else:
                fail_message = resp.get('err_code_des', 'default_error')
                cash_record.reason = fail_message
                cash_record.status = STATUS_FAIL
            cash_record.save()
            return cash_record
        except Exception as e:
            logging.exception(e)
        return None

    def create_red_packet(self, amount, reward_type, status=STATUS_USED, use_expire=True):
        rp = RedPacket()
        rp.amount = amount
        rp.status = status
        rp.reward_type = reward_type
        rp.expire = timezone.now()
        rp.belong = self.user
        if use_expire:
            rp.expire = timezone.now() + datetime.timedelta(minutes=20)
        rp.save()
        return rp

    def get_with_draw_list(self):
        cash = self.user.cash
        with_draw_list = []
        if cash < 29500:
            with_draw_list = [(30000, 40), (50000, 20), (100000, 10)]
        elif cash < 40000:
            with_draw_list = [(50000, 20), (100000, 10)]
        elif cash < 90000:
            with_draw_list = [(100000, 10)]
        return with_draw_list

    def get_possible_reward(self):
        with_draws = self.get_with_draw_list()
        _, ava_poss_tuple = zip(*with_draws)
        total_poss = 1 + sum(ava_poss_tuple)
        lucky_number = random.randint(1, 100)
        cash_range = 1.0 / total_poss * 100
        if lucky_number <= cash_range:
            amount = random.randint(1, 500)
            rp = self.create_red_packet(amount, PACKET_TYPE_CASH, False)
            self.user.cash += amount
            return rp
        pos_range = cash_range
        for itm in with_draws:
            pos_range += itm[1] / total_poss * 100
            if lucky_number <= pos_range:
                rp = self.create_red_packet(itm[0], PACKET_TYPE_WITHDRAW, STATUS_UNUSE)
                return rp
        # 兜底
        rp = self.create_red_packet(with_draws[-1][0], PACKET_TYPE_WITHDRAW, STATUS_UNUSE)
        return rp

    def handler_default(self, *args, **kwargs):
        rp = None
        amount = 0
        if self.user.check_point_draw:
            self.user.check_point_draw = False
            amount = 30
            # self.create_cash_record(amount)
            rp = self.create_red_packet(amount, PACKET_TYPE_WITHDRAW, STATUS_UNUSE)
        else:
            rp = self.get_possible_reward()
        self.user.cash += amount
        self.user.daily_reward_draw = False
        self.user.lucky_draw_total_count += 1
        self.user.lucky_draw_ava_withdraw += 1
        if self.user.lucky_draw_ava_withdraw == 7:
            self.user.check_point_draw = True
        self.user.save()
        return rp

    def handler_b(self, *args, **kwargs):
        rp = None
        amount = 0
        if self.user.daily_reward_count == 20 and self.user.right_count == 20:
            amount = 30
            rp = self.create_red_packet(amount, PACKET_TYPE_WITHDRAW, STATUS_UNUSE)
        elif self.user.check_point_draw:
            self.user.check_point_draw = False
            amount = 30
            # self.create_cash_record(amount)
            rp = self.create_red_packet(amount, PACKET_TYPE_WITHDRAW, STATUS_UNUSE)
        else:
            rp = self.get_possible_reward()
        self.user.cash += amount
        self.user.daily_reward_draw = False
        self.user.lucky_draw_total_count += 1
        self.user.lucky_draw_ava_withdraw += 1
        if self.user.lucky_draw_ava_withdraw == 7:
            self.user.check_point_draw = True
        self.user.save()
        return rp

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        if not self.user.daily_reward_draw:
            self.update_status(StatusCode.ERROR_REWARD_DENIED)
            return self.render_to_response()
        update_task_attr(self.user, 'daily_lucky_draw')
        rp = self.ab_test_handle('2003')
        return self.render_to_response({'reward': rp})
