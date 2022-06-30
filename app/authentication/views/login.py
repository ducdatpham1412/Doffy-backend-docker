from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from utilities.disableObject import DisableObject


class Login(GenericAPIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        # get object
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
            check = check_password(password, user.password)
            if not check:
                raise CustomError(error_message.login_fail,
                                  error_key.login_fail)
        except models.User.DoesNotExist:
            raise CustomError(error_message.login_fail, error_key.login_fail)

        # check is this user is temporary block
        try:
            # user temporary locking
            list_user_temporary_lock: list = DisableObject.get_disable_object(
                enums.disable_user)['list']
            list_user_temporary_lock.index(user.id)
            res = {
                'username': username,
                'isLocking': True,
            }
            return Response(res, status=status.HTTP_200_OK)
        except ValueError:
            # user is requesting delete account
            list_user_requesting_delete: list = DisableObject.get_disable_object(
                enums.disable_request_delete_account)['list']
            for request in list_user_requesting_delete:
                if request['userId'] == user.id and request['isActive'] == True:
                    res = {
                        'username': username,
                        'isLocking': True,
                    }
                    return Response(res, status=status.HTTP_200_OK)

        # login success
        return Response(user.tokens(), status=status.HTTP_200_OK)
