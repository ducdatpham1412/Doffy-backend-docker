from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from utilities import services
from datetime import timedelta
from utilities.disableObject import DisableObject
from rest_framework.response import Response
from rest_framework import status


class RequestDeleteAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        created_time = services.get_datetime_now()
        request_adding = {
            'userId': services.get_user_id_from_request(request),
            'createdTime': created_time,
            'deleteTime': created_time + timedelta(days=20),
            'isActive': True,
        }
        DisableObject.add_request_delete_account(request_adding)
        return Response(None, status=status.HTTP_200_OK)
