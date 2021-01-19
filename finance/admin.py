from django.contrib import admin
from django.forms import ModelForm

from finance.models import *

# Register your models here.

admin.site.register(ExchangeRecord)


class UserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['belong'].queryset = User.objects.filter(id=self.instance.belong.id).all()


class CashRecordAdmin(admin.ModelAdmin):
    list_display = ('belong', 'cash', 'create_time', 'status', 'reason')
    search_fields = ('belong',)
    form = UserForm


class RedPacketAdmin(admin.ModelAdmin):
    list_display = ('belong', 'amount', 'create_time', 'status', 'reward_type')
    search_fields = ('belong',)
    form = UserForm


class GameCashAdmin(admin.ModelAdmin):
    list_display = ('belong', 'cash', 'create_time', 'game_name', 'percentage')
    search_fields = ('belong',)
    form = UserForm


admin.site.register(CashRecord, CashRecordAdmin)
admin.site.register(RedPacket, RedPacketAdmin)
admin.site.register(GameCashRecord, GameCashAdmin)
