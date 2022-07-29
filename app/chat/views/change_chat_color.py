from bson.objectid import ObjectId
from utilities.exception.exception_handler import CustomError
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
import json
import requests


class ChangeChatColor(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)
        new_color = request.data['color']

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(conversation_id),
                'list_users': my_id
            },
            {
                '$set': {
                    'color': new_color,
                    'modified': services.get_datetime_now()
                }
            }
        )
        if not conversation:
            raise CustomError()

        requests.post('http://chat:1412/chat/change-chat-color', data=json.dumps({
            'conversationId': conversation_id,
            'color': new_color,
        }))

        return Response(None, status=status.HTTP_200_OK)
