import asyncio
import atexit
import functools
import json
import logging
import pywintypes
import re
import string
import subprocess
import websockets
import win32api

__version__ = '0.2.2'

g_logger_format = '%(asctime)s %(levelname)-8s %(message)s'


def multiple_replace(dict, text):
    pattern = re.compile("|".join(map(re.escape, dict.keys())))
    return pattern.sub(lambda mo: dict[mo.group(0)], text)


def show_one(text, all_proc):
    p = subprocess.Popen(['DM_Player.exe', text[:998]])  # at most 998 characters
    all_proc.append(p)
    while all_proc and all_proc[0].returncode is not None:
        all_proc.pop(0)


@functools.cache
def get_group_logger(group_name):
    logger = logging.Logger(group_name)
    logger.setLevel(logging.INFO)
    if any(c not in string.ascii_letters + string.digits + ' +-_,.@' for c in group_name):
        show_one(f'无法为 class_{group_name} 创建日志文件', [])
        logging.warning(f'无法为 class_{group_name} 创建日志文件')
        return logger
    handler = logging.FileHandler(f'class_{group_name}.log', mode='a', encoding='utf-8', delay=False)
    handler.setFormatter(logging.Formatter(g_logger_format))
    logger.handlers = [handler]
    return logger


async def client(apps, startswith_dm, all_proc):
    uri = f'wss://dmhunter.tsing.net/dmhunter/ws/chat/'
    subscribe_success = True
    while subscribe_success:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    'type': 'client.version',
                    'version': __version__,
                }))
                await websocket.send(json.dumps({
                    'type': 'client.subscribe',
                    'apps': [{'app_id': token['app_id'], 'client_token': token['token']} for token in apps],
                }))
                while True:
                    json_raw = await websocket.recv()
                    event = json.loads(json_raw)
                    if event['type'] == 'server.alert':
                        alert = event['alert']
                        logging.warning(alert)
                        show_one(alert, [])
                    elif event['type'] == 'server.subscribe_result':
                        subscribe_success = event['success']
                        if subscribe_success:
                            logging.info('subscribe success')
                            show_one('已连接弹幕服务器', all_proc)
                        else:
                            app_ids = [app['app_id'] for app in event['failed_apps']]
                            logging.warning(f'subscribe failed, failed_apps={app_ids!r}')
                            s = ', '.join([str(x) for x in app_ids])
                            show_one(f'Token {s} 错误，连接失败', [])
                            await websocket.close()
                            break
                    elif event['type'] == 'chat.mp_msg' or event['type'] == 'chat.qqun_msg':
                        if event['type'] == 'chat.mp_msg':
                            template = templates[1]
                            msg = event['mp_msg']
                            group_name = msg['group_name']
                            username = msg['openid']
                            if msg['user_filled_id']:
                                username += f'({msg["user_filled_id"]})'
                                template = templates[0]
                            content = msg['content']
                            text = multiple_replace({
                                    '{openid}': msg['openid'],
                                    '{id}': msg['user_filled_id'].strip(),
                                    '{content}': content.strip(),
                                }, template)
                        else:
                            msg = event['qqun_msg']
                            group_name = 'qqun'
                            username = f'{msg["card"] or msg["nickname"]}({msg["user_id"]})'
                            content = msg['message']
                            text = content.strip()
                        log_content = f'[{group_name}] {username}: {content}'
                        log_content_inline = log_content.replace('\n', r'\n').replace('\r', r'\r')
                        logging.info(log_content_inline)
                        get_group_logger(group_name).info(log_content_inline)
                        if text.upper().startswith('DM'):
                            show_one(text[2:].lstrip(), all_proc)
                            await asyncio.sleep(1)
                        elif not startswith_dm:
                            show_one(text, all_proc)
                            await asyncio.sleep(1)
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidHandshake):
            logging.warning('connection error, reconnect in 10 seconds')
            show_one('连接中断，10 秒后重连', all_proc)
            await asyncio.sleep(10)
            logging.info('reconnect')


if __name__ == '__main__':
    logging.basicConfig(
        format=g_logger_format,
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('console.log', mode='a', encoding='utf-8', delay=False),
        ]
    )

    all_proc = []

    @functools.cache
    def clear_proc():
        logging.info(f'dmhunter client v{__version__} exit')
        for p in all_proc:
            p.terminate()

    def ctrl_handler(ctrl_type):
        clear_proc()
        return 0

    logging.info(f'dmhunter client v{__version__} start')
    atexit.register(clear_proc)
    win32api.SetConsoleCtrlHandler(ctrl_handler)

    try:
        with open('templates.txt', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f'templates.txt not found')
        show_one('未找到 templates.txt', [])
        sys.exit()
    except UnicodeDecodeError:
        logging.error(f'templates unicode error')
        show_one('templates.txt 编码错误，应使用 UTF-8', [])
        sys.exit()
    if len(lines) < 2:
        logging.error(f'templates parsing error')
        show_one('templates.txt 格式错误', [])
        sys.exit()
    templates = [lines[0].strip(), lines[1].strip()]

    apps = []
    try:
        with open('tokens.txt', encoding='latin1') as f:
            for line in f:
                bom = '\xef\xbb\xbf'
                if line.startswith(bom):
                    line = line[len(bom):]
                if line.lstrip().startswith('#'):
                    continue
                s = line.split('#')[0].strip()
                app_id, token = s.split(':')
                app_id = int(app_id)
                apps.append({'app_id': app_id, 'token': token})
    except FileNotFoundError:
        logging.error(f'tokens.txt not found')
        show_one('未找到 tokens.txt', [])
        sys.exit()
    except ValueError:
        logging.error(f'token parsing error')
        show_one('Token 格式错误', [])
        sys.exit()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            client(apps, False, all_proc)
        )
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.error(str(e))
        show_one('弹幕客户端未知错误，已退出', [])
        raise
    except:
        logging.error('Unknown exception')
        show_one('弹幕客户端未知错误，已退出', [])
        raise
