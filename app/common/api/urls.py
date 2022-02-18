from django.urls.conf import path
from common.api import views


urlpatterns = [
    path('get-passport', views.GetPassport.as_view()),
    path('upload-image', views.UploadImage.as_view()),
    path('get-resource', views.GetResource.as_view()),
    path('update-my-bubbles', views.UpdateMyBubbles.as_view()),
    path('report-user/<int:user_id>', views.ReportUser.as_view())
]
