import base64
import channels.layers
import hashlib
import hmac
import json
import random
import re
import socket
import string
import struct
import time
import xml.etree.ElementTree as ET

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from Crypto.Cipher import AES
from . import consumers
from .helpers import *
from .models import *

# Create your views here.

def index(request):
    return render(request, 'dmhunter/index.html')

def mpinstall(request):
    if request.method == 'POST':
        if settings.USE_X_FORWARDED_HOST:
            host = request.META['HTTP_X_FORWARDED_HOST']
        else:
            host = request.META['HTTP_HOST']
        token = gen_token(32)
        aeskey = gen_token(43)
        with transaction.atomic():
            connector = Connector.objects.create(token=token, aeskey=aeskey)
            url = 'https://{:s}{:s}'.format(host, reverse('dmhunter:mpcallback', kwargs={'id': connector.id}))
            return render(request, 'dmhunter/mpinstall.html', {'id': connector.id, 'url': url, 'token': token, 'aeskey': aeskey})
    return render(request, 'dmhunter/mpinstall.html')

def qquninstall(request):
    if request.method == 'POST':
        verification_code = gen_token(16)
        client_token = gen_token(32)
        qqun_app = QqunApp.objects.create(group_id=None, verification_code=verification_code, client_token=client_token)
        return render(request, 'dmhunter/qquninstall.html', {'qq_dmrobot': settings.QQ_DMROBOT, 'id': qqun_app.id, 'verification_code': verification_code, 'client_token': client_token})
    return render(request, 'dmhunter/qquninstall.html', {'qq_dmrobot': settings.QQ_DMROBOT})

def webclient(request):
    return render(request, 'dmhunter/webclient.html')

@csrf_exempt
def mpcallback(request, id):
    connector = get_object_or_404(Connector.objects, id=id)
    token = connector.token
    aeskey = connector.aeskey

    signature = request.GET.get('signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    tmp_arr = sorted([token, timestamp, nonce])
    tmp_str = ''.join(tmp_arr)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()
    if tmp_str != signature:
        raise PermissionDenied

    if request.method == 'GET':
        return HttpResponse(request.GET.get('echostr', ''))

    et1 = ET.fromstring(request.body.decode())
    encrypt = et1.find('Encrypt').text
    key = base64.b64decode(aeskey + '=')
    cryptor = AES.new(key, AES.MODE_CBC, key[:16])
    plain_text = cryptor.decrypt(base64.b64decode(encrypt))
    content = plain_text[16:-plain_text[-1]]
    xml_len = socket.ntohl(struct.unpack('I',content[:4])[0])
    xml_content = content[4:xml_len + 4].decode()
    et2 = ET.fromstring(xml_content)

    from_appid = content[xml_len + 4:].decode()
    openid = request.GET['openid']
    to_user_name = et1.find('ToUserName').text
    from_user_name = et2.find('FromUserName').text
    create_time = int(et2.find('CreateTime').text)
    msg_type = et2.find('MsgType').text
    content = et2.find('Content')
    if content is not None:
        content = content.text
    else:
        content = ''
    msg_id = et2.find('MsgId')
    if msg_id is not None:
        msg_id = int(msg_id.text)
    else:
        msg_id = 0
    assert openid == from_user_name

    with transaction.atomic():
        gh_obj, _ = Gh.objects.get_or_create(appid=from_appid, defaults={'user_name': to_user_name})
        openid_obj, _ = Openid.objects.get_or_create(openid=openid, defaults={'gh': gh_obj})
        message_obj = Message.objects.create(openid=openid_obj, gh=gh_obj, from_appid=from_appid, to_user_name=to_user_name, from_user_name=from_user_name, create_time=create_time, msg_type=msg_type, content=content, msg_id=msg_id, xml_content=xml_content)
    assert openid_obj.gh == gh_obj

    reply = None

    if content.lstrip().startswith('@'):
        m1 = re.match('@register\s*=', content)
        m2 = re.match('\s*@(class|id)\s*[=＝]', content.lower())
        m3 = re.match('@gettoken\s*=', content)
        if m1:
            name = content[len(m1.group(0)):].strip()
            regular_name = Group.regularize(name)
            if regular_name:
                if Group.objects.filter(gh=gh_obj, regular_name=regular_name).exists():
                    reply = '注册失败：名称被占用'
                else:
                    with transaction.atomic():
                        subscription = Subscription.objects.create(token=gen_token(16))
                        Group.objects.create(gh=gh_obj, name=name, regular_name=regular_name, owner=openid_obj, subscription=subscription)
                    reply = f'成功注册新频道 {name}'
            else:
                reply = '注册失败：名称应使用字母、数字、空格、减号、下划线、小数点'
        elif m2:
            action = m2.group(1).lower()
            name = content[len(m2.group(0)):].strip()
            if action == 'class':
                if not name:
                    openid_obj.joined_group = None
                    openid_obj.save()
                    reply = '已退出频道'
                else:
                    regular_name = Group.regularize(name)
                    if regular_name:
                        group = Group.objects.filter(gh=gh_obj, regular_name=regular_name).first()
                        if group:
                            openid_obj.joined_group = group
                            openid_obj.save()
                            reply = f'成功加入频道 {group.name}'
                            if name != group.name:
                                reply += '（不区分大小写）'
                        else:
                            reply = '加入失败：频道不存在'
                    else:
                        reply = '加入失败：频道名称格式错误'
            else:  # action == 'id'
                is_charset_valid = all(c in string.digits + string.ascii_letters for c in name)
                if not is_charset_valid:
                    reply = 'ID 格式错误，只允许字母数字'
                elif len(name) > 18:
                    reply = 'ID 过长'
                else:
                    if name:
                        reply = '更新 ID 成功'
                    else:
                        reply = '删除 ID 成功'
                    openid_obj.user_filled_id = name
                    openid_obj.full_clean()
                    openid_obj.save()
        elif m3:
            name = content[len(m3.group(0)):].strip()
            regular_name = Group.regularize(name)
            if regular_name:
                group = Group.objects.filter(gh=gh_obj, regular_name=regular_name).first()
                if group.owner == openid_obj:
                    reply = f'{group.subscription.id}:{group.subscription.token}'
                else:
                    reply = '获取 token 失败：权限错误'
            else:
                reply = '获取 token 失败：频道名称错误'
        elif content.strip() == '@class':
            group = openid_obj.joined_group
            if openid_obj.joined_group:
                reply = f'当前弹幕频道为 {openid_obj.joined_group.name}'
            else:
                reply = '未加入弹幕频道'
        else:
            reply = '指令错误'
    elif content:
        if openid_obj.joined_group:
            group_name = 'dmhunter_chat_{:d}'.format(openid_obj.joined_group.subscription.id)
            if consumers.group_channel_names[group_name]:
                message_obj.group = openid_obj.joined_group  # delayed save. save with reply at the same time
                channel_layer = channels.layers.get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'broadcast',
                        'message': {
                            'type': 'chat.mp_msg',
                            'mp_msg': {
                                'group_name': openid_obj.joined_group.name,
                                'openid': openid,
                                'user_filled_id': openid_obj.user_filled_id,
                                'msg_type': msg_type,
                                'content': content,
                            },
                        },
                    }
                )
                reply = '弹幕发射~升空！'
            else:
                reply = '当前频道未接收弹幕'
        else:
            reply = '未加入弹幕频道'

    if reply:
        message_obj.reply=reply
        message_obj.save()

    if reply:
        xml = ET.Element('xml')
        timestamp = int(time.time())
        child = ET.SubElement(xml, 'ToUserName')
        child.text = openid
        child = ET.SubElement(xml, 'FromUserName')
        child.text = to_user_name
        child = ET.SubElement(xml, 'CreateTime')
        child.text = str(timestamp)
        child = ET.SubElement(xml, 'MsgType')
        child.text = 'text'
        child = ET.SubElement(xml, 'Content')
        child.text = reply
        text = ET.tostring(xml, encoding='utf-8')

        text = gen_token(16).encode() + struct.pack('I', socket.htonl(len(text))) + text + from_appid.encode()
        text_length = len(text)
        block_size = 32
        amount_to_pad = block_size - (text_length % block_size)
        if amount_to_pad == 0:
            amount_to_pad = block_size
        text += bytes([amount_to_pad] * amount_to_pad)
        cryptor = AES.new(key, AES.MODE_CBC, key[:16])
        text = base64.b64encode(cryptor.encrypt(text)).decode()
        tmp_arr = sorted([token, str(timestamp), nonce, text])
        tmp_str = ''.join(tmp_arr)
        signature = hashlib.sha1(tmp_str.encode()).hexdigest()

        xml = ET.Element('xml')
        child = ET.SubElement(xml, 'Encrypt')
        child.text = text
        child = ET.SubElement(xml, 'MsgSignature')
        child.text = signature
        child = ET.SubElement(xml, 'TimeStamp')
        child.text = str(timestamp)
        child = ET.SubElement(xml, 'Nonce')
        child.text = nonce
        text = ET.tostring(xml, encoding='utf-8')
        return HttpResponse(text)
    else:
        return HttpResponse('success')

@csrf_exempt
def cqhttpcallback(request):
    if request.method == 'POST':
        sig = hmac.new(settings.CQHTTP_SECRET, request.body, 'sha1').hexdigest()
        sig_recv = request.headers.get('X-Signature')
        if sig_recv is None or sig_recv[len('sha1='):] != sig:
            return HttpResponseBadRequest()
        data = json.loads(request.body.decode('utf-8'))
        if data['post_type'] == 'request' and data.get('sub_type') != 'add':
            return JsonResponse({'approve': True})
        if data['post_type'] == 'message' and data['message_type'] == 'group':
            message = data['message']
            qqun_app = QqunApp.objects.filter(verification_code=message, group_id__isnull=True)
            if qqun_app:
                with transaction.atomic():
                    QqunApp.objects.filter(group_id=data['group_id']).delete()
                    qqun_app.update(group_id=data['group_id'])
                return JsonResponse({'reply': '弹幕绑定成功'})
            qqun_app = QqunApp.objects.filter(group_id=data['group_id']).first()
            if qqun_app:
                qqun_message = QqunMsg.objects.create(
                    app=qqun_app,
                    group_id=data['group_id'],
                    time=data['time'],
                    self_id=data['self_id'],
                    sub_type=data['sub_type'],
                    message_id=data['message_id'],
                    user_id=data['user_id'],
                    message=data['message'],
                    sender_nickname=data['sender'].get('nickname'),
                    sender_card=data['sender'].get('card'),
                    body=request.body.decode('utf-8'),
                )
                channel_layer = channels.layers.get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'dmhunter_chat_{:d}'.format(qqun_app.id),
                    {
                        'type': 'broadcast',
                        'message': {
                            'type': 'chat.qqun_msg',
                            'qqun_msg': {
                                'sub_type': data['sub_type'],
                                'user_id': data['user_id'],
                                'nickname': data['sender'].get('nickname'),
                                'card': data['sender'].get('card'),
                                'message': friendly_message(message),
                            },
                        },
                    }
                )
        return HttpResponse()
    return HttpResponseBadRequest()
