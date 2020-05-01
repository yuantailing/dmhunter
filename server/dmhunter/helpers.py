import random
import re
import string

_cq_sub = [
    (re.compile(r'\[CQ\:image,[^\]]*\]'), '[图片]'),
    (re.compile(r'\[CQ\:record,[^\]]*\]'), '[语音]'),
    (re.compile(r'\[CQ\:contact,[^\]]*\]'), '[名片]'),
    (re.compile(r'\[CQ\:face,id=(\d+)\]'), lambda m: f'[表情{m.group(1)}]'),
    (re.compile(r'\[CQ\:at,qq=(\d+)\]'), lambda m: f'@{m.group(1)} '),
    (re.compile(r'\[CQ\:[^\]]*\]'), '[特殊消息]'),
]

def friendly_message(message):
    for pattern, target in _cq_sub:
        message = pattern.sub(target, message)
    return message

def gen_token(length):
    sigma = string.digits + string.ascii_letters
    rd = random.SystemRandom()
    return ''.join([rd.choice(sigma) for _ in range(length)])
