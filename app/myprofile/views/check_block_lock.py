from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting.models import Block
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
from authentication.query.user_request import CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT
from findme.mysql import mysql_select
from django.db.models import Q


class CheckIsBlockOrLockAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_had_been_blocked(self, my_id, your_id):
        try:
            Block.objects.get(Q(block=my_id, blocked=your_id)
                              | Q(block=your_id, blocked=my_id))
            return True
        except Block.DoesNotExist:
            return False

    def check_is_locking_account(self, your_id):
        user_requests = mysql_select(
            CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT(user_id=your_id))

        if not user_requests:
            return False

        for request in user_requests:
            if request['type'] == enums.request_user_lock_account:
                return True
            elif request['type'] == enums.request_user_delete_account and request['expired'] > services.get_datetime_now():
                return True

        return False

    def get(self, request, id):
        my_id = services.get_user_id_from_request(request)
        if self.check_had_been_blocked(my_id=my_id, your_id=id) or self.check_is_locking_account(your_id=id):
            raise CustomError()
        return Response(None, status=status.HTTP_200_OK)
