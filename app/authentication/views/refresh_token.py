from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework.response import Response
from rest_framework import status


class MyRefreshToken(GenericAPIView):
    def post(self, request):
        refreshToken = request.data['refresh']
        try:
            refresh = RefreshToken(refreshToken)
        except TokenError:
            raise CustomError(error_message.token_blacklisted,
                              error_key.token_blacklisted)

        res = {
            'access': str(refresh.access_token)
        }
        return Response(res, status=status.HTTP_200_OK)
