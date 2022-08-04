from authentication.models import User
from bson.objectid import ObjectId
from common.serializers import GetPassportSerializer
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.renderers import PagingRenderer
import pymongo


class GetListMessages(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_avatar_and_name(self, user_id):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        return {
            'avatar': passport['profile']['avatar'],
            'name': passport['profile']['name']
        }

    def get(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        # Get info from "chat_conversation"
        conversation = mongoDb.chat_conversation.find_one({
            '_id': ObjectId(conversation_id)
        })
        object_avatar_name = {}
        for user_id in conversation['list_users']:
            avatar_name = self.get_avatar_and_name(
                user_id=user_id
            )
            object_avatar_name[user_id] = avatar_name
        total_messages = conversation['total_messages']

        # Get from "message" collection
        list_messages = mongoDb.chat_message.find(
            {
                'conversation_id': conversation_id,
                'status': enums.status_active
            }
        ).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)

        data_messages = []
        for message in list_messages:
            if message['type'] == enums.message_image:
                for index, value in enumerate(message['content']):
                    message['content'][index] = services.create_link_image(
                        value)

            created = services.get_local_string_date_time(
                message['created'])

            relationship = enums.relationship_self if message[
                'creator'] == my_id else enums.relationship_not_know

            content = message['content']
            if message['type'] == enums.message_join_community:
                content = object_avatar_name[message['creator']]['name']

            temp = {
                'id': str(message.pop('_id')),
                'type': message['type'],
                'content': content,
                'creator': message['creator'],
                'creatorAvatar': object_avatar_name[message['creator']]['avatar'],
                'creatorName': object_avatar_name[message['creator']]['name'],
                'created': created,
                'relationship': relationship,
            }

            data_messages.append(temp)

        # Response
        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_messages,
            'data': data_messages
        }

        return Response(res, status=status.HTTP_200_OK)
