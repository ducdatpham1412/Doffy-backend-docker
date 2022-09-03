from django.urls.conf import path
from common.views import bubble_profile, passport, resource, upload, report, comment, notification, people_like


urlpatterns = [
    path('get-passport', passport.GetPassport.as_view()),
    path('upload-file', upload.UploadImage.as_view()),
    path('get-resource', resource.GetResource.as_view()),
    path('report-user/<int:user_id>', report.ReportUser.as_view()),
    path('get-list-bubble-profile',
         bubble_profile.GetListBubbleProfile.as_view()),
    path('get-list-bubble-profile-enjoy',
         bubble_profile.GetListBubbleProfileOfUserEnjoy.as_view()),
    path('detail-bubble-profile/<str:post_id>',
         bubble_profile.GetDetailBubbleProfile.as_view()),
    path('detail-bubble-profile-enjoy/<str:post_id>',
         bubble_profile.GetDetailBubbleProfileEnjoy.as_view()),
    path('list-people-react/<str:post_id>',
         people_like.GetListPeopleLike.as_view()),
    path('list-comments/<str:post_id>', comment.GetListComment.as_view()),
    path('delete-comment/<str:comment_id>', comment.DeleteComment.as_view()),
    path('list-notifications', notification.GestListNotification.as_view()),
    path('read-notification/<str:notification_id>',
         notification.ReadNotification.as_view()),
    # like and un-like comment here
]
