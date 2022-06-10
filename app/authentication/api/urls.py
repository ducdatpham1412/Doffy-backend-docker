from django.urls.conf import path
from authentication.api.next_views.login_faceboook import SocialLogin
from authentication.api import views


urlpatterns = [
    path('request-otp', views.RequestOTP.as_view()),
    path('check-otp', views.CheckOTP.as_view()),
    path('register', views.Register.as_view()),
    path('login', views.Login.as_view()),
    path('login-social', SocialLogin.as_view()),
    path('refresh-token', views.MyRefreshToken.as_view()),
    path('log-out', views.Logout.as_view()),
    path('reset-password', views.ResetPassword.as_view()),
    path('verify-token', views.VerifyToken.as_view()),
    path('get-id-enjoy-mode', views.GetIdEnjoyMode.as_view()),
    path('lock-account', views.LockAccount.as_view()),
    path('open-account', views.OpenAccount.as_view()),
    path('delete-account', views.RequestDeleteAccount.as_view())
]
