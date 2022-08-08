from bson.objectid import ObjectId
from utilities.exception.exception_handler import CustomError
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from utilities.enums import message_change_color, status_active
import json
import requests
from myprofile.models import Profile


class ChangeChatColor(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)
        new_color = request.data['color']
        now = services.get_datetime_now()

        # Update modify of conversation
        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(conversation_id),
                'list_users': my_id
            },
            {
                '$set': {
                    'color': new_color,
                    'modified': now
                }
            }
        )
        if not conversation:
            raise CustomError()

        # Insert new message and send to socket
        insert_message = {
            'type': message_change_color,
            'content': '',
            'creator': my_id,
            'created': now,
            'conversation_id': conversation_id,
            'status': status_active
        }
        mongoDb.chat_message.insert_one(insert_message)

        profile = Profile.objects.get(user=my_id)
        if not profile:
            raise CustomError()

        socket_message = {
            'id': str(insert_message['_id']),
            'conversationId': conversation_id,
            'type': message_change_color,
            'content': "",
            'creator': my_id,
            'creatorName': profile.name,
            'creatorAvatar': services.create_link_image(profile.avatar),
            'tag': None,
            'created': str(now)
        }

        requests.post('http://chat:1412/chat/change-chat-color', data=json.dumps({
            'conversationId': conversation_id,
            'color': new_color,
            'newMessage': socket_message,
        }))

        return Response(None, status=status.HTTP_200_OK)
