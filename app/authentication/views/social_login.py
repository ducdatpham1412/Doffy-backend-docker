from rest_framework import status
from rest_framework.generics import GenericAPIView
from utilities import enums
from authentication import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from authentication.models import User
import requests
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from django.conf import settings
from jwt.exceptions import PyJWTError
import jwt
import time


def check_and_sign_in(email: str):
    try:
        user = User.objects.get(email=email)
        return {
            'isNewUser': False,
            **user.tokens()
        }
    except User.DoesNotExist:
        register_data = {
            email,
        }
        serializer = serializers.RegisterSerializer(data=register_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return {
            'isNewUser': True,
            **user.tokens()
        }


class GoogleTokenAuthentication():
    GOOGLE_ID_TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'

    def do_auth(self, id_token: str, os: int):
        res = requests.get(self.GOOGLE_ID_TOKEN_INFO_URL, params={
            'id_token': id_token
        })

        if not res.ok:
            raise CustomError()
        res = res.json()

        check_audience = ''
        if os == enums.os_iOS:
            check_audience = settings.IOS_GOOGLE_OAUTH2_CLIENT_ID
        elif os == enums.os_android:
            check_audience = settings.ANDROID_GOOGLE_OAUTH2_CLIENT_ID

        if res['aud'] != check_audience:
            raise CustomError(error_message.login_fail, error_key.login_fail)

        return check_and_sign_in(email=res['email'])


class AppleIdAuthentication():
    ACCESS_TOKEN_URL = 'https://appleid.apple.com/auth/token'
    JWK_URL = 'https://appleid.apple.com/auth/keys'
    AUD_URL = 'https://appleid.apple.com'
    TOKEN_TTL_SEC = 5 * 60

    def get_key_and_secret(self):
        headers = {
            'kid': settings.SOCIAL_AUTH_APPLE_KEY_ID
        }
        time_now = int(time.time())
        payload = {
            'iss': settings.SOCIAL_AUTH_APPLE_TEAM_ID,
            'iat': time_now,
            'exp': time_now + self.TOKEN_TTL_SEC,
            'aud': self.AUD_URL,
            'sub': settings.CLIENT_ID,
        }

        client_secret = jwt.encode(
            payload=payload,
            key=settings.SOCIAL_AUTH_APPLE_PRIVATE_KEY,
            algorithm='ES256',
            headers=headers
        )

        return settings.CLIENT_ID, client_secret

    def decode_id_token(self, id_token: str):
        try:
            decoded = jwt.decode(
                id_token,
                audience=settings.CLIENT_ID,
                options={
                    'verify_signature': False
                }
            )
            return decoded
        except PyJWTError:
            raise CustomError()

    def do_auth(self, authorization_code: str):
        client_id, client_secret = self.get_key_and_secret()
        headers = {
            'content-type': "application/x-www-form-urlencoded"
        }
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
        }

        res = requests.post(self.ACCESS_TOKEN_URL,
                            data=data, headers=headers)
        response_dict = res.json()
        id_token = response_dict.get('id_token', None)
        if not id_token:
            raise CustomError()

        email = self.decode_id_token(id_token=id_token).get('email', None)
        if not email:
            raise CustomError()

        return check_and_sign_in(email=email)


class SocialLogin(GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.headers.get('Authorization')
        provider = request.data['provider']
        os = request.data['os']

        if provider == enums.sign_in_google:
            res = GoogleTokenAuthentication().do_auth(id_token=id_token, os=os)

        if provider == enums.sign_in_apple:
            res = AppleIdAuthentication().do_auth(authorization_code=id_token)

        else:
            raise CustomError(error_message.login_fail, error_key.login_fail)

        return Response(res, status=status.HTTP_200_OK)
