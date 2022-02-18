from django.urls import path
from . import views


urlpatterns = [
    path('get-list-chat-tag', views.GetListChatTags.as_view()),
    path('get-detail-chat-tag/<str:chat_tag_id>',
         views.GetDetailChatTag.as_view()),
    path('get-list-messages/<str:chat_tag>', views.GetListMessages.as_view()),
    path('change-group-name/<str:chat_tag>',
         views.ChangeGroupNameChatTag.as_view()),
    path('list-info-user', views.GetListUserInfo.as_view()),
    path('delete-message/<str:id_message>', views.DeleteMessage.as_view())
]

# handle chat tag
#     path('handle-chat-tag', views.HandleChatTag.as_view()),
#     path('handle-chat-tag-enjoy', views.HandleChatTagEnjoy.as_view()),

# handle bubble palace
#     path('handle-bubble-palace', views.HandleBubblePalace.as_view()),
# path('handle-bubble-palace-enjoy', views.HandleBubblePlaceForEnjoy.as_view()),

#     path('request-public/<str:chat_tag>', views.RequestPublic.as_view()),
# path('agree-request-public/<str:chat_tag>',
#      views.AgreeRequestPublic.as_view()),

#     path('send-message', views.HandleMessage.as_view()),
