from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utilities import services
from utilities.disableObject import DisableObject
from utilities import enums
from rest_framework import status


class LockAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        id = services.get_user_id_from_request(request)
        DisableObject.add_disable_user(enums.disable_user, id)
        return Response(None, status=status.HTTP_200_OK)
