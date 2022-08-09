from django.urls.conf import path
from myprofile.views import profile, follow, post, notification, check_block_lock


urlpatterns = [
    path('get-profile/<int:id>', profile.GetProfile.as_view()),
    path('edit-profile', profile.EditProfile.as_view()),
    path('follow/<int:id>', follow.FollowUser.as_view()),
    path('un-follow/<int:id>', follow.UnFollowUser.as_view()),
    path('follow/get-list/<int:user_id>', follow.GetListFollow.as_view()),
    path('create-post', post.CreatePost.as_view()),
    path('edit-post/<str:post_id>', post.EditPost.as_view()),
    path('delete-post/<str:post_id>', post.DeletePost.as_view()),
    path('list-posts/<int:user_id>', post.GetListPost.as_view()),
    path('like-post/<str:post_id>', post.LikePost.as_view()),
    path('unlike-post/<str:post_id>', post.UnLikePost.as_view()),
    path('get-list-notifications', notification.GetListNotification.as_view()),
    path('check-block-lock-account/<int:id>',
         check_block_lock.CheckIsBlockOrLockAccount.as_view()),
    # path('edit-group/<str:group_id>', views.EditGroup.as_view()),
    # path('create-group', views.CreateGroup.as_view()),
    # path('list-my-groups', views.GetMyListGroups.as_view()),
    # path('delete-group/<str:group_id>', views.DeleteGroup.as_view()),
]
