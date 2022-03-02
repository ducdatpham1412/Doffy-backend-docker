from django.urls import path
from . import views


urlpatterns = [
    path('get-list-chat-tag', views.GetListChatTags.as_view()),
    path('get-detail-chat-tag/<str:chat_tag_id>',
         views.GetDetailChatTag.as_view()),
    path('get-list-messages/<str:chat_tag>', views.GetListMessages.as_view()),
    path('change-group-name/<str:chat_tag>',
         views.ChangeGroupNameChatTag.as_view()),
    path('change-chat-color/<str:chat_tag>', views.ChangeChatColor.as_view()),
    path('list-info-user', views.GetListUserInfo.as_view()),
    path('delete-message', views.DeleteMessage.as_view())
]
