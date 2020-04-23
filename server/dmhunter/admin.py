from django.contrib import admin

from .helpers import friendly_message
from .models import MpApp, MpMsg, QqunApp, QqunMsg

# Register your models here.

class MpAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', )

class MpMsgAdmin(admin.ModelAdmin):
    list_display = ('id', 'app', 'openid', 'to_user_name', 'msg_type', 'content', 'created_at', )
    list_filter = ('to_user_name', 'msg_type', )

class QqunAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_id', 'created_at', )

class QqunMsgAdmin(admin.ModelAdmin):
    def show_message(inst):
        return friendly_message(inst.message)
    list_display = ('id', 'group_id', 'sub_type', 'user_id', 'sender_nickname', show_message, 'created_at', )
    list_filter = ('group_id', 'sub_type', 'user_id', 'sender_nickname', )

admin.site.register(MpApp, MpAppAdmin)
admin.site.register(MpMsg, MpMsgAdmin)
admin.site.register(QqunApp, QqunAppAdmin)
admin.site.register(QqunMsg, QqunMsgAdmin)
