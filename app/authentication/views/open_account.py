from rest_framework.generics import GenericAPIView
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities.disableObject import DisableObject
from rest_framework.response import Response
from django.db.models import Q
from utilities import enums
from rest_framework import status
from findme.mysql import mysql_select, mysql_update
from authentication.query import verify_code


class OpenAccount(GenericAPIView):
    def put(self, request):
        username = request.data['username']
        code = request.data['verifyCode']

        # verify
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
        except models.User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

        otp_code = mysql_select(
            verify_code.SEARCH_OTP(username=username, code=code))

        if not otp_code:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)
        mysql_update(verify_code.UPDATE_OTP(username=username, code=0))

        DisableObject.remove_disable_user(enums.disable_user, user.id)
        DisableObject.disable_request_delete_account(user.id)

        return Response(None, status=status.HTTP_200_OK)
