from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from utilities import services, enums
from rest_framework.response import Response
from rest_framework import status
from findme.mysql import mysql_insert
from authentication.query.user_request import ADD_USER_REQUEST


class RequestDeleteAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        my_id = services.get_user_id_from_request(request)
        mysql_insert(ADD_USER_REQUEST(
            user_id=my_id, type=enums.request_user_delete_account))
        return Response(None, status=status.HTTP_200_OK)
