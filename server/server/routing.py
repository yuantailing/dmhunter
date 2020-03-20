from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

import dmhunter.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path(r'dmhunter/', URLRouter(dmhunter.routing.websocket_urlpatterns)),
        ])
    ),
})
