from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services


class ChangeGroupNameChatTag(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag):
        myId = services.get_user_id_from_request(request)
        new_name = request.data['name']
        chat_tag_id = ObjectId(chat_tag)

        mongoDb.chatTag.find_one_and_update(
            {
                '_id': chat_tag_id,
                'listUser': myId
            },
            {
                '$set': {
                    'groupName': new_name,
                    'updateTime': services.get_datetime_now()
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)
