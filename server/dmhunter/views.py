import base64
import channels.layers
import hashlib
import json
import random
import socket
import string
import struct
import time
import xml.etree.ElementTree as ET

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from Crypto.Cipher import AES
from .models import *

# Create your views here.

def index(request):
    return render(request, 'dmhunter/index.html')

def mpinstall(request):
    if request.method == 'POST':
        def gen_token(length):
            sigma = string.digits + string.ascii_letters
            rd = random.SystemRandom()
            return ''.join([rd.choice(sigma) for _ in range(length)])

        if settings.USE_X_FORWARDED_HOST:
            host = request.META['HTTP_X_FORWARDED_HOST']
        else:
            host = request.META['HTTP_HOST']
        if host != 'dmhunter.tsing.net':
            return HttpResponseBadRequest('请使用域名 dmhunter.tsing.net 访问本网站')
        token = gen_token(32)
        aeskey = gen_token(43)
        client_token = gen_token(32)
        mp_app = MpApp.objects.create(token=token, aeskey=aeskey, client_token=client_token)
        url = 'https://{:s}{:s}'.format(host, reverse('dmhunter:mpcallback', kwargs={'id': mp_app.id}))
        return render(request, 'dmhunter/mpinstall.html', {'id': mp_app.id, 'url': url, 'token': token, 'aeskey': aeskey, 'client_token': client_token})
    return render(request, 'dmhunter/mpinstall.html')

def webclient(request):
    return render(request, 'dmhunter/webclient.html')

@csrf_exempt
def mpcallback(request, id):
    mp_app = get_object_or_404(MpApp.objects, id=id)
    token = mp_app.token
    aeskey = mp_app.aeskey

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
    msg_id = int(et2.find('MsgId').text)
    MpMsg.objects.create(app=mp_app, from_appid=from_appid, openid=openid, to_user_name=to_user_name, from_user_name=from_user_name, create_time=create_time, msg_type=msg_type, content=content, msg_id=msg_id)
    assert openid == from_user_name

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'dmhunter_chat_{:d}'.format(mp_app.id),
        {
            'type': 'broadcast',
            'message': {
                'type': 'chat.mp_msg',
                'mp_msg': {
                    'openid': openid,
                    'msg_type': msg_type,
                    'content': content,
                },
            },
        }
    )

    if content.lstrip().upper().startswith('DM'):
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
        child.text = '弹幕发射~升空！'
        text = ET.tostring(xml, encoding='utf-8')

        def gen_token(length):
            sigma = string.digits + string.ascii_letters
            rd = random.SystemRandom()
            return ''.join([rd.choice(sigma) for _ in range(length)])

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
