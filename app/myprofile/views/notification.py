from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


class GetListNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        page_index = int(request.query_params['pageIndex'])
        take = int(request.query_params['take'])

        start = int((page_index-1) * take)
        end = int(page_index * take)

        data_notification = mongoDb.notification.find_one({
            'userId': my_id
        })
        res = data_notification['list'][start:end]

        return Response(res, status=status.HTTP_200_OK)
