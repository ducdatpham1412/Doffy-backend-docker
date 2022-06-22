from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


class ChangeChatColor(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag):
        my_id = services.get_user_id_from_request(request)
        new_color = request.data['color']

        mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(chat_tag),
                'listUser': my_id
            },
            {
                '$set': {
                    'color': new_color,
                    'updateTime': services.get_datetime_now()
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)
