from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.renderers import PagingRenderer


class GestListNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        data_notification = mongoDb.notification.find_one({
            'userId': my_id
        })

        totals = len(data_notification['list'])
        start = (page_index-1) * take
        end = page_index * take

        data = data_notification['list'][start:end]

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': totals,
            'data': data,
        }

        return Response(res, status=status.HTTP_200_OK)


class ReadNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, notification_id):
        my_id = services.get_user_id_from_request(request)

        mongoDb.notification.update_one(
            {
                'userId': my_id,
                'list.id': notification_id
            },
            {
                '$set': {
                    'list.$.hadRead': True,
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)
