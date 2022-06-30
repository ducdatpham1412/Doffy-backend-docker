from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from utilities.exception import error_message, error_key
from rest_framework_simplejwt.exceptions import TokenError
from utilities.exception.exception_handler import CustomError
from rest_framework import status


class Logout(GenericAPIView):
    def post(self, request):
        refreshToken = request.data['refreshToken']
        try:
            RefreshToken(refreshToken).blacklist()
        except TokenError:
            raise CustomError(error_message.token_blacklisted,
                              error_key.token_blacklisted)

        return Response(None, status=status.HTTP_200_OK)
