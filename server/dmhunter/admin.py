from django.contrib import admin

from .helpers import friendly_message
from .models import *

# Register your models here.

class ConnectorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', )

class GhAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'appid', 'user_name', 'created_at', )

class OpenidAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'openid', 'gh', 'user_filled_id', 'joined_group', )
    list_filter = ('gh', 'joined_group', )

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', )

class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'gh', 'name', 'regular_name', 'owner', )
    list_filter = ('gh', 'name', )

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user_name', 'to_user_name', 'group', 'msg_type', 'content', 'reply', 'created_at', )
    list_filter = ('to_user_name', 'group', 'msg_type', 'from_user_name', )

admin.site.register(Connector, ConnectorAdmin)
admin.site.register(Gh, GhAdmin)
admin.site.register(Openid, OpenidAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Message, MessageAdmin)
