from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.exception.exception_handler import CustomError
import requests
import json


class ChangeConversationName(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)
        new_name = request.data['name']

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(conversation_id),
                'list_users': my_id
            },
            {
                '$set': {
                    'conversation_name': new_name,
                    'modified': services.get_datetime_now()
                }
            }
        )
        if not conversation:
            raise CustomError()

        requests.post('http://chat:1412/chat/change-chat-name', data=json.dumps({
            'conversationId': conversation_id,
            'name': new_name,
        }))

        return Response(None, status=status.HTTP_200_OK)
