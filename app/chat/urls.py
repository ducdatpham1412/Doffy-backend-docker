from chat.views import (get_detail_chat_tag, get_list_chat_tag,
                        get_list_messages, change_chat_color, get_list_user_info, change_channel_name, delete_message, check_procedure)
from django.urls import path


urlpatterns = [
    path('get-list-chat-tag', get_list_chat_tag.GetListChatTags.as_view()),
    path('get-detail-chat-tag/<str:chat_tag_id>',
         get_detail_chat_tag.GetDetailChatTag.as_view()),
    path('get-list-messages/<str:chat_tag>',
         get_list_messages.GetListMessages.as_view()),
    path('change-group-name/<str:chat_tag>',
         change_channel_name.ChangeGroupNameChatTag.as_view()),
    path('change-chat-color/<str:chat_tag>',
         change_chat_color.ChangeChatColor.as_view()),
    path('list-info-user', get_list_user_info.GetListUserInfo.as_view()),
    path('delete-message', delete_message.DeleteMessage.as_view()),
    # path('check-procedure', check_procedure.CheckProcedure.as_view())
]
