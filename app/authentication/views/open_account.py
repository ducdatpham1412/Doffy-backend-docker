from rest_framework.generics import GenericAPIView
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities.disableObject import DisableObject
from rest_framework.response import Response
from django.db.models import Q
from utilities import enums
from rest_framework import status


class OpenAccount(GenericAPIView):
    def put(self, request):
        username = request.data['username']
        verify_code = request.data['verifyCode']

        # verify
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
        except models.User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

        try:
            models.VerifyCode.objects.get(
                username=username, code=verify_code)
        except models.VerifyCode.DoesNotExist:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        DisableObject.remove_disable_user(enums.disable_user, user.id)
        DisableObject.disable_request_delete_account(user.id)

        return Response(None, status=status.HTTP_200_OK)
