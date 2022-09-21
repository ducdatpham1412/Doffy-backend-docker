from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication import models
from utilities.services import get_user_id_from_request, get_object
from utilities.enums import status_active, account_shop, account_user
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from utilities.exception.exception_handler import CustomError


class UpgradeAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        my_id = get_user_id_from_request(request)
        location = get_object(request.data, 'location')
        if not location:
            raise CustomError()

        user = models.User.objects.get(id=my_id, is_active=status_active)
        if user.account_type == account_user:
            raise CustomError()
        user.account_type = account_shop
        user.save()

        return Response(None, status=status.HTTP_200_OK)
