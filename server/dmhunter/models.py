from django.db import models

# Create your models here.

class App(models.Model):
    client_token = models.CharField(max_length=64, db_index=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MpApp(App):
    token = models.CharField(max_length=64, db_index=True, unique=True, default=None)
    aeskey = models.CharField(max_length=64, db_index=True, unique=True, default=None)

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
    xml_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QqunApp(App):
    group_id = models.BigIntegerField(db_index=True, unique=True, null=True)
    verification_code = models.CharField(max_length=64, db_index=True, unique=True)

class QqunMsg(models.Model):
    app = models.ForeignKey(QqunApp, on_delete=models.PROTECT)
    group_id = models.BigIntegerField(db_index=True)
    time = models.BigIntegerField()
    self_id = models.BigIntegerField()
    sub_type = models.CharField(max_length=64, db_index=True)
    message_id = models.IntegerField()
    user_id = models.BigIntegerField(db_index=True)
    message = models.TextField()
    sender_card = models.TextField(null=True)
    sender_nickname = models.TextField(null=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
