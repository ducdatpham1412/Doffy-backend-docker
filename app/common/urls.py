from django.urls.conf import path
from common.views import bubble_profile, passport, resource, upload, report, comment, notification, people_like, top_reputations, edit_history


urlpatterns = [
    path('get-passport', passport.GetPassport.as_view()),
    path('upload-file', upload.UploadImage.as_view()),
    path('get-resource', resource.GetResource.as_view()),
    path('report-user/<int:user_id>', report.ReportUser.as_view()),
    path('get-list-bubble-profile',
         bubble_profile.GetListBubbleProfile.as_view()),
    path('detail-bubble-profile/<str:post_id>',
         bubble_profile.GetDetailBubbleProfile.as_view()),
    path('list-edit-history/<str:post_id>',
         edit_history.GetListEditHistory.as_view()),
    path('list-people-react/<str:post_id>',
         people_like.GetListPeopleLike.as_view()),
    path('list-comments/<str:post_id>', comment.GetListComment.as_view()),
    path('delete-comment/<str:comment_id>', comment.DeleteComment.as_view()),
    path('list-notifications', notification.GestListNotification.as_view()),
    path('read-notification/<str:notification_id>',
         notification.ReadNotification.as_view()),
    path('get-top-reputations', top_reputations.GetListTopReputation.as_view()),
    path('get-top-group-buying', bubble_profile.GetListTopGroupBuying.as_view()),
    # api for purchase
    # path('create-purchase', purchase.CreatePurchase.as_view()),
    # path('confirm-purchased', purchase.ConfirmPurchase.as_view())
]
