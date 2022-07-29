from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
import requests
import json


class DeleteMessage(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, message_id):
        my_id = services.get_user_id_from_request(request)

        message = mongoDb.chat_message.find_one_and_update(
            {
                '_id': ObjectId(message_id),
                'creator': my_id
            },
            {
                '$set': {
                    'status': enums.status_not_active
                }
            }
        )
        if not message:
            raise CustomError(error_message.not_have_permission_delete_message,
                              error_key.not_have_permission_delete_message)

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(message['conversation_id'])
            },
            {
                '$inc': {
                    'totalMessages': -1
                }
            }
        )
        if not conversation:
            raise CustomError()

        requests.post('http://chat:1412/chat/delete-message', data=json.dumps({
            'conversationId': message['conversation_id'],
            'messageId': message_id,
        }))

        return Response(None, status=status.HTTP_200_OK)
