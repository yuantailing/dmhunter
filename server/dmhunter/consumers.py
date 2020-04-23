import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import App


class ChatConsumer(WebsocketConsumer):
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
            app = App.objects.filter(id=self.app_id).first()
            auth_success = bool(app and data['client_token'] == app.client_token)
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
            else:
                self.close()

    # Receive message from room group
    def broadcast(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))
