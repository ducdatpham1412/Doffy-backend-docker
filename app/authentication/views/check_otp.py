from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework import status
from findme.mysql import mysql_select, mysql_update
from authentication.query import verify_code


class CheckOTP(GenericAPIView):
    def post(self, request):
        username = request.data['username']
        code = int(request.data['code'])

        if (code == 0):
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        otp_code = mysql_select(
            verify_code.SEARCH_OTP(username=username, code=code))

        if not otp_code:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        mysql_update(verify_code.UPDATE_OTP(username=username, code=0))

        return Response(None, status=status.HTTP_200_OK)
