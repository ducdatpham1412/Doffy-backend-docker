from django.urls.conf import path
from authentication.views import request_otp, check_otp, register, login, social_login, log_out, refresh_token, reset_password, verify_token, get_id_enjoy_mode, lock_account, open_account, request_delete_acc, _test, tiki_personal, tiki_campaign


urlpatterns = [
    path('request-otp', request_otp.RequestOTP.as_view()),
    path('check-otp', check_otp.CheckOTP.as_view()),
    path('register', register.Register.as_view()),
    path('login', login.Login.as_view()),
    path('login-social', social_login.SocialLogin.as_view()),
    path('refresh-token', refresh_token.MyRefreshToken.as_view()),
    path('log-out', log_out.Logout.as_view()),
    path('reset-password', reset_password.ResetPassword.as_view()),
    path('verify-token', verify_token.VerifyToken.as_view()),
    path('get-id-enjoy-mode', get_id_enjoy_mode.GetIdEnjoyMode.as_view()),
    path('lock-account', lock_account.LockAccount.as_view()),
    path('open-account', open_account.OpenAccount.as_view()),
    path('delete-account', request_delete_acc.RequestDeleteAccount.as_view()),
    # Tiki hackathon api
    path('tiki-personal', tiki_personal.TikiPersonal.as_view()),
    path('tiki-campaign', tiki_campaign.TikiCampaign.as_view())
]
