from authentication.models import User
from common import serializers
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


class GetPassport(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        id = services.get_user_id_from_request(request)
        user = User.objects.get(id=id)
        passport = serializers.GetPassportSerializer(user).data

        data_notification = mongoDb.notification.find_one({
            'userId': id,
        })
        number_new_notifications = 0
        for notification in data_notification['list'][0:29]:
            if not notification['hadRead']:
                number_new_notifications += 1
        res = {
            **passport,
            'numberNewNotifications': number_new_notifications,
        }

        return Response(res, status=status.HTTP_200_OK)
