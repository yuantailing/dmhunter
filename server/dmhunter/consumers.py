import json
import pkg_resources

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from collections import defaultdict

from .models import Subscription


group_channel_names = defaultdict(set)

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.groups = set()
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        for room_group_name in self.groups:
            async_to_sync(self.channel_layer.group_discard)(
                room_group_name,
                self.channel_name
            )
            group_channel_names[room_group_name].discard(self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'client.version':
            self.client_version = data['version']
            version = pkg_resources.parse_version(self.client_version)
            if version < pkg_resources.parse_version('0.2'):
                self.send(text_data=json.dumps({
                    'type': 'server.alert',
                    'alert': '弹幕客户端有更新，见 https://dmhunter.tsing.net/',
                }))
            if version > pkg_resources.parse_version('0.2.2'):
                self.send(text_data=json.dumps({
                    'type': 'server.alert',
                    'alert': '弹幕客户端版本过高',
                }))
        elif data['type'] == 'client.subscribe':
            assert isinstance(self.client_version, str)
            success = len(data['apps']) > 0
            failed_apps = []
            for o in data['apps']:
                app = Subscription.objects.filter(id=o['app_id']).first()
                if not app or o['client_token'] != app.token:
                    success = False
                    failed_apps.append({'app_id': o['app_id']})
                else:
                    room_group_name = 'dmhunter_chat_{:d}'.format(app.id)
                    if room_group_name not in self.groups:
                        async_to_sync(self.channel_layer.group_add)(
                            room_group_name,
                            self.channel_name
                        )
                        self.groups.add(room_group_name)
                        group_channel_names[room_group_name].add(self.channel_name)
            self.send(text_data=json.dumps({
                'type': 'server.subscribe_result',
                'success': success,
                'failed_apps': failed_apps,
            }))
            if not success:
                self.close()
        else:
            self.send(text_data=json.dumps({
                'type': 'server.warning',
                'warning': 'unknown event type',
            }))
            self.close()

    # Receive message from room group
    def broadcast(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))


class ChatConsumer_0_1_0(WebsocketConsumer):
    def connect(self):
        self.app_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = 'dmhunter_chat_{:d}'.format(self.app_id)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        group_channel_names[self.room_group_name].discard(self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'client.version':
            self.client_version = data['version']
            if self.client_version != '0.1.0':
                self.send(text_data=json.dumps({
                    'type': 'server.alert',
                    'alert': '弹幕客户端有更新，见 https://dmhunter.tsing.net/',
                }))
        elif data['type'] == 'client.auth':
            assert isinstance(self.client_version, str)
            app = Subscription.objects.filter(id=self.app_id).first()
            auth_success = bool(app and data['client_token'] == app.token)
            self.send(text_data=json.dumps({
                'type': 'server.auth_result',
                'auth_success': auth_success,
            }))
            if auth_success:
                # Join room group
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )
                group_channel_names[self.room_group_name].add(self.channel_name)
            else:
                self.close()

    # Receive message from room group
    def broadcast(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))
