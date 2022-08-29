from authentication.models import User
from common import serializers
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.enums import status_notification_not_read


class GetPassport(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        id = services.get_user_id_from_request(request)
        user = User.objects.get(id=id)
        passport = serializers.GetPassportSerializer(user).data

        number_new_notifications = mongoDb.notification.count({
            'user_id': id,
            'status': status_notification_not_read
        })

        res = {
            **passport,
            'numberNewNotifications': number_new_notifications,
        }

        return Response(res, status=status.HTTP_200_OK)
