from django.db import models

# Create your models here.

class MpApp(models.Model):
    token = models.CharField(max_length=64, db_index=True, unique=True, default=None)
    aeskey = models.CharField(max_length=64, db_index=True, unique=True, default=None)
    client_token = models.CharField(max_length=64, db_index=True, unique=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MpMsg(models.Model):
    app = models.ForeignKey(MpApp, on_delete=models.PROTECT)
    from_appid = models.CharField(max_length=64, db_index=True, default=None)
    openid = models.CharField(max_length=64, db_index=True, default=None)
    to_user_name = models.CharField(max_length=64, db_index=True, default=None)
    from_user_name = models.CharField(max_length=64, db_index=True, default=None)
    create_time = models.BigIntegerField(db_index=True, default=None)
    msg_type = models.CharField(max_length=64, db_index=True, default=None)
    content = models.TextField()
    msg_id = models.BigIntegerField(db_index=True, unique=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
