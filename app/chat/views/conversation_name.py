from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.enums import message_change_name, status_active
from utilities.exception.exception_handler import CustomError
import requests
import json
from myprofile.models import Profile


class ChangeConversationName(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)
        new_name = request.data['name']
        now = services.get_datetime_now()

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(conversation_id),
                'list_users': my_id
            },
            {
                '$set': {
                    'conversation_name': new_name,
                    'modified': now
                }
            }
        )
        if not conversation:
            raise CustomError()

        # Insert message and send to socket
        insert_message = {
            'type': message_change_name,
            'content': '',
            'creator': my_id,
            'created': now,
            'conversation_id': conversation_id,
            'status': status_active,
        }
        mongoDb.chat_message.insert_one(insert_message)

        profile = Profile.objects.get(user=my_id)
        socket_message = {
            'id': str(insert_message['_id']),
            'conversationId': conversation_id,
            'type':  message_change_name,
            'content': "",
            'creator': my_id,
            'creatorName': profile.name,
            'creatorAvatar': services.create_link_image(profile.avatar),
            'tag': None,
            'created': str(now)
        }

        requests.post('http://chat:1412/chat/change-chat-name', data=json.dumps({
            'conversationId': conversation_id,
            'name': new_name,
            'newMessage': socket_message,
        }))

        return Response(None, status=status.HTTP_200_OK)
