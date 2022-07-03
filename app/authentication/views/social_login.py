from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums
from authentication import serializers
from rest_framework.permissions import AllowAny
from utilities import services
from django.conf import settings
from social_django.utils import load_backend, load_strategy
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden, AuthAlreadyAssociated
from requests.exceptions import HTTPError
from social_core.backends.oauth import BaseOAuth2
from rest_framework.response import Response


class SocialLogin(GenericAPIView):
    serializer_class = serializers.SocialSerializer
    permission_classes = [AllowAny]

    def sign_in_google(self, id_token: str, os: int):
        res = services.google_validate_id_token(id_token)
        audience = res['aud']
        check_audience = ''
        if os == enums.os_iOS:
            check_audience = settings.IOS_GOOGLE_OAUTH2_CLIENT_ID
        elif os == enums.os_android:
            check_audience = settings.ANDROID_GOOGLE_OAUTH2_CLIENT_ID

        if audience == check_audience:
            try:
                user = models.User.objects.get(google_acc=res['email'])
                return {
                    'isNewUser': False,
                    **user.tokens()
                }
            # If not exist, register
            except models.User.DoesNotExist:
                register_data = {
                    'google_acc': res['email'],
                }
                serializer = serializers.RegisterSerializer(data=register_data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                return {
                    'isNewUser': True,
                    **user.tokens()
                }
        else:
            raise CustomError(error_message.login_fail, error_key.login_fail)

    def sign_in_facebook_google(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.data.get('provider', None)
        strategy = load_strategy(request)

        # Load backend
        try:
            backend = load_backend(
                strategy=strategy, name=provider, redirect_uri=None)
        except MissingBackend:
            raise CustomError(error_message.login_facebook_failed,
                              error_key.login_facebook_failed)

        # Get user
        try:
            if isinstance(backend, BaseOAuth2):
                access_token = serializer.data.get('access_token', None)
            user = backend.do_auth(access_token=access_token)
        except HTTPError:
            raise CustomError(error_message.login_facebook_failed,
                              error_key.login_facebook_failed)
        except AuthTokenError:
            raise CustomError(error_message.login_facebook_failed,
                              error_key.login_facebook_failed)

        # Authenticate user
        try:
            authenticated_user = backend.do_auth(
                access_token=access_token, user=user)
        except HTTPError:
            raise CustomError(error_message.login_facebook_failed,
                              error_key.login_facebook_failed)
        except AuthForbidden:
            raise CustomError(error_message.login_facebook_failed,
                              error_key.login_facebook_failed)
        except AuthAlreadyAssociated:
            print('continue login')

        if authenticated_user and authenticated_user.is_active:
            print('login successfully: ', authenticated_user)

        return Response('Hello, ', status=status.HTTP_200_OK)

    def sign_in_apple(self, id_token: str):
        apple_authenticated = models.AppleIdAuth()
        check = apple_authenticated.do_auth(access_token=id_token)
        print('check is: ', check)

    def post(self, request):
        id_token = request.headers.get('Authorization')
        provider = request.data['provider']
        os = request.data['os']

        if provider == enums.sign_in_google:
            res = self.sign_in_google(id_token=id_token, os=os)

        if provider == enums.sign_in_apple:
            res = self.sign_in_apple(id_token=id_token)

        return Response(res, status=status.HTTP_200_OK)
