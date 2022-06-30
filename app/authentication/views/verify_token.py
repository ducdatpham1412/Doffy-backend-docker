from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from utilities import services
from rest_framework.response import Response
from rest_framework import status


class VerifyToken(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        id = services.get_user_id_from_request(request)
        return Response(id, status=status.HTTP_200_OK)
