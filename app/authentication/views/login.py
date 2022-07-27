from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums, services
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from findme.mysql import mysql_select, mysql_update
from authentication.query.user_request import CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT
from authentication.query.user import UN_ACTIVE_ACCOUNT


class Login(GenericAPIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        # Get object
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
            check = check_password(password, user.password)
            if not check:
                raise CustomError(error_message.login_fail,
                                  error_key.login_fail)
        except models.User.DoesNotExist:
            raise CustomError(error_message.login_fail, error_key.login_fail)

        # Check is user requesting delete or block account
        user_request = mysql_select(
            CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT(user_id=user.id))
        if user_request:
            for request in user_request:
                if request['type'] == enums.request_user_lock_account:
                    res = {
                        'username': username,
                        'isLocking': True
                    }
                    return Response(res, status=status.HTTP_200_OK)
                elif request['type'] == enums.request_user_delete_account:
                    if request['expired'] > services.get_datetime_now():
                        res = {
                            'username': username,
                            'isLocking': True
                        }
                        return Response(res, status=status.HTTP_200_OK)
                    elif request['expired'] < services.get_datetime_now():
                        mysql_update(UN_ACTIVE_ACCOUNT(user_id=user.id))
                        raise CustomError(error_message.login_fail,
                                          error_key.login_fail)

        # Login success
        return Response(user.tokens(), status=status.HTTP_200_OK)
