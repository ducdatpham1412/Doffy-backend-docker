from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from authentication.api import serializers
from social_django.utils import load_backend, load_strategy
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden, AuthAlreadyAssociated
from requests.exceptions import HTTPError
from social_core.backends.oauth import BaseOAuth2
from utilities import enums


class SocialLogin(GenericAPIView):
    serializer_class = serializers.SocialSerializer
    permission_classes = [permissions.AllowAny]

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
                access_token = serializer.data.get('access_token')
            user = backend.do_auth(access_token)
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

    def sign_in_apple(self, request):
        return {}

    def post(self, request):
        provider = request.data['provider']

        if provider == enums.sign_in_facebook or provider == enums.sign_in_google:
            res = self.sign_in_facebook_google(request)
        else:
            res = {}

        return Response(res, status=status.HTTP_200_OK)
