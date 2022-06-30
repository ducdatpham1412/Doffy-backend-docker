from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework import status


class CheckOTP(GenericAPIView):
    def get_object(self, username, code):
        try:
            return models.VerifyCode.objects.get(username=username, code=code)
        except models.VerifyCode.DoesNotExist:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

    def post(self, request):
        username = request.data['username']
        code = int(request.data['code'])

        if (code == 0):
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        verify_code = self.get_object(username, code)
        verify_code.code = 0
        verify_code.save()

        return Response(None, status=status.HTTP_200_OK)
