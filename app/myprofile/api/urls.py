from django.urls.conf import path
from myprofile.api import views


urlpatterns = [
    path('get-profile/<int:id>', views.GetProfile.as_view()),
    path('edit-profile', views.EditProfile.as_view()),
    path('follow/enable/<int:id>', views.FollowUser.as_view()),
    path('follow/disable/<int:id>', views.UnFollowUser.as_view()),
    path('create-post', views.CreatePost.as_view()),
    path('edit-post/<str:post_id>', views.EditPost.as_view()),
    path('delete-post/<str:post_id>', views.DeletePost.as_view()),
    path('list-posts/<int:user_id>', views.GetListPost.as_view()),
    path('like-post/<str:post_id>', views.LikePost.as_view()),
    path('unlike-post/<str:post_id>', views.UnLikePost.as_view()),
    path('follow/get-list/<int:user_id>', views.GetListFollow.as_view()),
    path('get-list-notifications', views.GetListNotification.as_view())
]
