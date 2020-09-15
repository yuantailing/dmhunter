# Generated by Django 3.1.1 on 2020-09-13 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Connector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(default=None, max_length=64, unique=True)),
                ('aeskey', models.CharField(default=None, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Gh',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appid', models.CharField(default=None, max_length=64, unique=True)),
                ('user_name', models.CharField(default=None, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=64)),
                ('regular_name', models.CharField(default=None, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gh', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.gh')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(default=None, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Openid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openid', models.CharField(default=None, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gh', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.gh')),
                ('joined_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dmhunter.group')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_appid', models.CharField(db_index=True, default=None, max_length=64)),
                ('to_user_name', models.CharField(db_index=True, default=None, max_length=64)),
                ('from_user_name', models.CharField(db_index=True, default=None, max_length=64)),
                ('create_time', models.BigIntegerField()),
                ('msg_type', models.CharField(db_index=True, default=None, max_length=64)),
                ('content', models.TextField()),
                ('msg_id', models.BigIntegerField(unique=True)),
                ('xml_content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gh', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.gh')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dmhunter.group')),
                ('openid', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.openid')),
            ],
        ),
        migrations.AddField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.openid'),
        ),
        migrations.AddField(
            model_name='group',
            name='subscription',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='dmhunter.subscription'),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together={('gh', 'regular_name')},
        ),
    ]