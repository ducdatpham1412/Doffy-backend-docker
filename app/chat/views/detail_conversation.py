from authentication.models import User
from bson.objectid import ObjectId
from common.api.serializers import GetPassportSerializer
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting.models import Block
from utilities import enums, services
from django.db.models import Q


class GetDetailConversation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_info_of_member(self, user_id):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        return {
            'id': user_id,
            'name': passport['profile']['name'],
            'avatar': passport['profile']['avatar'],
            'gender': passport['information']['gender']
        }

    def check_is_block(self, my_id, list_user_id: list) -> bool:
        your_id = None
        for user_id in list_user_id:
            if (user_id != my_id):
                your_id = user_id

        # is me
        if your_id == None:
            return False

        try:
            Block.objects.get(Q(block=my_id, blocked=your_id)
                              | Q(block=your_id, blocked=my_id))
        except Block.DoesNotExist:
            return False

        return True

    def get(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)

        conversation = mongoDb.chat_conversation.find_one({
            '_id': ObjectId(conversation_id)
        })

        info_list_users = []
        for user_id in conversation['list_users']:
            info_list_users.append(self.get_info_of_member(user_id))

        user_data = {}
        for key in conversation['user_data']:
            data = conversation['user_data'][key]
            user_data[key] = {
                'created': str(data['created']),
                'modified': str(data['modified'])
            }

        is_blocked = self.check_is_block(
            my_id=my_id, list_user_id=conversation['list_users'])

        res = {
            'id': str(conversation['_id']),
            'listUser': info_list_users,
            'conversationName': conversation['conversation_name'],
            'conversationImage': conversation['conversation_image'],
            'latestMessage': conversation['latest_message'],
            'userData': user_data,
            'color': conversation['color'],
            'modified': str(conversation['modified']),
            'status': conversation['status'],
            'isBlocked': is_blocked,
        }

        return Response(res, status=status.HTTP_200_OK)
