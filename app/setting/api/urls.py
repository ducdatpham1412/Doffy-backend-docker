from django.urls.conf import path
from setting.api import views


urlpatterns = [
    path('security/change-password', views.ChangePassword.as_view()),
    path('extend/change-theme', views.ChangeTheme.as_view()),
    path('extend/change-language', views.ChangeLanguage.as_view()),
    path('extend/change-display-avatar', views.ChangeDisplayAvatar.as_view()),
    path('block/<int:id>', views.BlockUser.as_view()),
    path('unblock/<int:id>', views.UnblockUser.as_view()),
    path('stop-conversation/<str:conversation_id>',
         views.StopConversation.as_view()),
    path('open-conversation/<str:conversation_id>',
         views.OpenConversation.as_view()),
    path('block/get-list', views.GetListBlock.as_view()),
    path('change-information', views.ChangeInformation.as_view()),
]
