from rest_framework.generics import GenericAPIView
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework.response import Response
from django.db.models import Q
from utilities import enums, services
from rest_framework import status
from findme.mysql import mysql_select, mysql_update
from authentication.query.verify_code import SEARCH_OTP, UPDATE_OTP
from authentication.query.user_request import UN_ACTIVE_REQUEST_USER, CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT
from authentication.query.user import UN_ACTIVE_ACCOUNT


class OpenAccount(GenericAPIView):
    def put(self, request):
        username = request.data['username']
        code = request.data['verifyCode']

        # Check user is exist and active
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
        except models.User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

        # Check user is requesting delete / lock account
        # If request-delete expired, un active user
        user_requests = mysql_select(
            CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT(user_id=user.id))
        if not user_requests:
            raise CustomError()
        for request in user_requests:
            if request['type'] == enums.request_user_delete_account and request['expired'] < services.get_datetime_now():
                mysql_update(UN_ACTIVE_ACCOUNT(user_id=user.id))
                raise CustomError()

        # Check verify code
        otp_code = mysql_select(
            SEARCH_OTP(username=username, code=code))
        if not otp_code:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)
        mysql_update(UPDATE_OTP(username=username, code=0))

        # If verify code's valid, un active request
        mysql_update(UN_ACTIVE_REQUEST_USER(user_id=user.id))

        return Response(None, status=status.HTTP_200_OK)
