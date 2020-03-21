import asyncio
import json
import logging
import subprocess
import websockets
import pywintypes
import win32api

__version__ = '0.1.0'

def show_one(text, all_proc):
    p = subprocess.Popen(['DM_Player.exe', text])
    all_proc.append(p)
    while all_proc[0].returncode is not None:
        all_proc.pop(0)

async def client(mp_app_id, token, startswith_dm, all_proc):
    uri = f'wss://dmhunter.tsing.net/dmhunter/ws/chat/{mp_app_id}/'
    auth_success = True
    while auth_success:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    'type': 'client.version',
                    'version': __version__,
                }))
                await websocket.send(json.dumps({
                    'type': 'client.auth',
                    'client_token': token,
                }))
                while True:
                    json_raw = await websocket.recv()
                    msg = json.loads(json_raw)
                    if msg['type'] == 'server.alert':
                        alert = msg['alert']
                        logging.warning(alert)
                        show_one(alert, [])
                    elif msg['type'] == 'server.auth_result':
                        auth_success = msg['auth_success']
                        if auth_success:
                            logging.info('auth success')
                            show_one('已连接弹幕服务器', all_proc)
                        else:
                            logging.warning('auth failed')
                            show_one('Token 错误，连接失败', [])
                            await websocket.close()
                            break
                    elif msg['type'] == 'chat.mp_msg':
                        mp_msg = msg['mp_msg']
                        openid = mp_msg['openid']
                        content = mp_msg['content']
                        content_inline = content.replace('\n', r'\n').replace('\r', r'\r')
                        logging.info(f'{openid}: {content_inline}')
                        text = content.strip()
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
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('console.log', mode='a', encoding='utf-8', delay=False),
        ]
    )

    all_proc = []
    def ctrl_handler(ctrl_type):
        logging.info(f'dmhunter client v{__version__} exit')
        for p in all_proc:
            p.terminate()
        return 0
    logging.info(f'dmhunter client v{__version__} start')
    win32api.SetConsoleCtrlHandler(ctrl_handler)

    try:
        with open('token.txt') as f:
            mp_app_id, token = f.read().strip().split(':')
            mp_app_id = int(mp_app_id)
    except FileNotFoundError:
        show_one('未找到 token.txt', [])
        exit()
    except ValueError:
        show_one('Token 格式错误', [])
        exit()
    try:
        asyncio.get_event_loop().run_until_complete(client(mp_app_id, token, False, all_proc))
    except KeyboardInterrupt:
        pass
