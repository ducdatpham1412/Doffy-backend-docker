from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from utilities import enums
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from social_core.backends.oauth import BaseOAuth2
from django.conf import settings
from datetime import datetime, timedelta
from social_core.utils import handle_http_errors


class User(AbstractUser):
    username = None
    is_superuser = None
    is_staff = None
    first_name = None
    last_name = None
    groups = None
    user_permissions = None

    facebook = models.CharField(default='', max_length=200)
    email = models.EmailField(default='',)
    phone = models.CharField(default='', max_length=enums.PHONE_MAX_LENGTH)
    password = models.CharField(max_length=enums.PASSWORD_MAX_LENGTH)

    USERNAME_FIELD = 'id'

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'token': str(refresh.access_token),
            'refreshToken': str(refresh)
        }


class VerifyCode(models.Model):
    username = models.TextField()
    # type = models.SmallIntegerField()
    code = models.SmallIntegerField()

    def __str__(self):
        return str(self.code)


class AppleIdAuth(BaseOAuth2):
    name = 'apple'
    ACCESS_TOKEN_URL = 'https://appleid.apple.com/auth/token'
    SCOPE_SEPARATOR = ','
    ID_KEY = 'uid'

    def get_key_and_secret(self):
        headers = {
            'kid': settings.SOCIAL_AUTH_APPLE_KEY_ID
        }

        time_now = datetime.now()
        payload = {
            'iss': settings.SOCIAL_AUTH_APPLE_TEAM_ID,
            'iat': time_now,
            'exp': time_now + timedelta(days=180),
            'aud': 'https://appleid.apple.com',
            'sub': settings.CLIENT_ID,
        }

        client_secret = jwt.encode(
            payload=payload,
            key=settings.SOCIAL_AUTH_APPLE_PRIVATE_KEY,
            algorithm='ES256',
            headers=headers
        )

        return settings.CLIENT_ID, client_secret

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        response_data = {}
        client_id, client_secret = self.get_key_and_secret()
        headers = {
            'content-type': "application/x-www-form-urlencoded"
        }
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': access_token,
            'grant_type': 'authorization_code',
        }

        res = requests.post(AppleIdAuth.ACCESS_TOKEN_URL,
                            data=data, headers=headers)
        response_dict = res.json()
        id_token = response_dict.get('id_token', None)

        if id_token:
            decoded = jwt.decode(id_token, '', verify=False)
            response_data.update(
                {'email': decoded['email']}) if 'email' in decoded else None
            response_data.update(
                {'uid': decoded['sub']}) if 'sub' in decoded else None

        response = kwargs.get('response') or {}
        response.update(response_data)
        response.update({'access_token': access_token}
                        ) if 'access_token' not in response else None

        kwargs.update({'response': response, 'backend': self})

        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        email = response.get('email', None)
        details = {
            'email': email,
        }
        return details
