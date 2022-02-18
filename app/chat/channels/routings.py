from django.urls import re_path
from . import bubble_chattag_consumer, message_consumer


bubble_chattag_consumer = bubble_chattag_consumer.BubbleAndChatTag().as_asgi()
message_consumer = message_consumer.MessageDetail().as_asgi()

websocket_urlpatterns = [
    # bubble_palace and chat_tag
    re_path(r'ws/doffy-socket/bubble-chattag/(?P<user_id>\w+)',
            bubble_chattag_consumer),

    # chat_detail
    re_path(r'ws/doffy-socket/chat-detail/(?P<user_id>\w+)', message_consumer)
]
