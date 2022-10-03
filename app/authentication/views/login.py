from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums, services
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from findme.mysql import mysql_update
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
        user_request = services.get_list_requests_delete_or_block_account(
            user_id=user.id)
        if user_request:
            for request in user_request:
                if request['type'] == enums.request_user_lock_account:
                    res = {
                        'username': username,
                        'isLocking': True
                    }
                    return Response(res, status=status.HTTP_200_OK)
                elif request['type'] == enums.request_user_delete_account:
                    if services.format_utc_time(request['expired']) > services.get_utc_now():
                        res = {
                            'username': username,
                            'isLocking': True
                        }
                        return Response(res, status=status.HTTP_200_OK)
                    elif services.format_utc_time(request['expired']) < services.get_utc_now():
                        mysql_update(UN_ACTIVE_ACCOUNT(user_id=user.id))
                        raise CustomError(error_message.login_fail,
                                          error_key.login_fail)

        # Login success
        return Response(user.tokens(), status=status.HTTP_200_OK)
