from django.urls.conf import path
from common.api import views


urlpatterns = [
    path('get-passport', views.GetPassport.as_view()),
    path('upload-image', views.UploadImage.as_view()),
    path('get-resource', views.GetResource.as_view()),
    path('update-my-bubbles', views.UpdateMyBubbles.as_view()),
    path('report-user/<int:user_id>', views.ReportUser.as_view()),
    path('get-list-bubble-profile', views.GetListBubbleProfile.as_view()),
    path('get-list-bubble-profile-enjoy',
         views.GetListBubbleProfileOfUserEnjoy.as_view()),
    path('detail-bubble-profile/<str:bubble_id>',
         views.GetDetailBubbleProfile.as_view()),
    path('detail-bubble-profile-enjoy/<str:bubble_id>',
         views.GetDetailBubbleProfileEnjoy.as_view()),
    path('list-comments/<str:bubble_id>', views.GetListComment.as_view()),
    path('add-comment/<str:bubble_id>', views.AddComment.as_view()),
    path('list-notifications', views.GestListNotification.as_view()),
    path('read-notification/<str:notification_id>',
         views.ReadNotification.as_view())
]
