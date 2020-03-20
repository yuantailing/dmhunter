from django.contrib import admin

from .models import MpApp, MpMsg

# Register your models here.

class MpAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', )

class MpMsgAdmin(admin.ModelAdmin):
    list_display = ('id', 'app', 'openid', 'to_user_name', 'msg_type', 'content', 'created_at', )
    list_filter = ('to_user_name', 'msg_type', )

admin.site.register(MpApp, MpAppAdmin)
admin.site.register(MpMsg, MpMsgAdmin)
