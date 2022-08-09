from chat.views import (detail_conversation, list_conversations,
                        list_messages, change_chat_color, conversation_name, delete_message, get_list_user_info)
from django.urls import path


urlpatterns = [
    path('list-conversations',
         list_conversations.GetListConversations.as_view()),
    path('detail-conversation/<str:conversation_id>',
         detail_conversation.GetDetailConversation.as_view()),
    path('list-messages/<str:conversation_id>',
         list_messages.GetListMessages.as_view()),
    path('change-chat-name/<str:conversation_id>',
         conversation_name.ChangeConversationName.as_view()),
    path('change-chat-color/<str:conversation_id>',
         change_chat_color.ChangeChatColor.as_view()),
    path('list-info-user', get_list_user_info.GetListUserInfo.as_view()),
    path('delete-message/<str:message_id>',
         delete_message.DeleteMessage.as_view()),
]
