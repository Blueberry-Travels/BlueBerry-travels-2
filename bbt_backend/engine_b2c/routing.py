from django.urls import re_path
from engine_b2c import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/collab/(?P<group_id>[0-9a-f-]+)/$',
        consumers.CollabChatConsumer.as_asgi(),
    ),
]