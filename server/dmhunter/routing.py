from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path(r'ws/chat/', consumers.ChatConsumer),
    path(r'ws/chat/<int:id>/', consumers.ChatConsumer_0_1_0),
]
