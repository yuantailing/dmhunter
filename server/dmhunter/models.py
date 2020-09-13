import re

from django.db import models

# Create your models here.

class Connector(models.Model):
    token = models.CharField(max_length=64, unique=True, default=None)
    aeskey = models.CharField(max_length=64, unique=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Gh(models.Model):
    appid = models.CharField(max_length=64, unique=True, default=None)
    user_name = models.CharField(max_length=64, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Openid(models.Model):
    openid = models.CharField(max_length=64, unique=True, default=None)
    gh = models.ForeignKey(Gh, on_delete=models.PROTECT)
    joined_group = models.ForeignKey('Group', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Subscription(models.Model):
    token = models.CharField(max_length=64, unique=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Group(models.Model):
    gh = models.ForeignKey(Gh, on_delete=models.PROTECT)
    name = models.CharField(max_length=64, default=None)
    regular_name = models.CharField(max_length=64, unique=True, default=None)
    owner = models.ForeignKey(Openid, on_delete=models.PROTECT)
    subscription = models.OneToOneField(Subscription, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    pattern_regular_name = re.compile('^[0-9A-Za-z \-_\.]+$')
    @classmethod
    def regularize(cls, name):
        m = cls.pattern_regular_name.match(name)
        if not m or name != name.strip() or '  ' in name:
           return None
        return name.lower()

    class Meta:
        unique_together = ('gh', 'regular_name', )


class Message(models.Model):
    openid = models.ForeignKey(Openid, on_delete=models.PROTECT)
    gh = models.ForeignKey(Gh, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.PROTECT)
    from_appid = models.CharField(max_length=64, db_index=True, default=None)
    to_user_name = models.CharField(max_length=64, db_index=True, default=None)
    from_user_name = models.CharField(max_length=64, db_index=True, default=None)
    create_time = models.BigIntegerField()
    msg_type = models.CharField(max_length=64, db_index=True, default=None)
    content = models.TextField()
    msg_id = models.BigIntegerField(unique=True)
    xml_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
