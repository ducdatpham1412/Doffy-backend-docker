from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utilities.services import get_user_id_from_request
from utilities.enums import request_user_lock_account
from rest_framework import status
from authentication.models import User_Request, User
from datetime import timedelta
from utilities.exception.exception_handler import CustomError
from utilities.services import get_utc_now


class LockAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CustomError()

    def put(self, request):
        my_id = get_user_id_from_request(request)
        user = self.get_user(user_id=my_id)
        now = get_utc_now()
        expired = now + timedelta(days=20)

        user_request = User_Request(
            creator=user, type=request_user_lock_account, created=now, expired=expired)
        user_request.save()

        return Response(None, status=status.HTTP_200_OK)
