import random
import re
import string

def friendly_message(message):
    return re.sub(r'\[CQ\:image,[^\]]*\]', '[图片]', message)

def gen_token(length):
    sigma = string.digits + string.ascii_letters
    rd = random.SystemRandom()
    return ''.join([rd.choice(sigma) for _ in range(length)])
