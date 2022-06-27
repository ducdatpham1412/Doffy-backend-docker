from authentication.models import User
from bson.objectid import ObjectId
from common.api.serializers import GetPassportSerializer
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

    def get_avatar_and_name(self, user_id, is_chattag_private):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        if not is_chattag_private:
            return {
                'avatar': passport['profile']['avatar'],
                'name': passport['profile']['name']
            }

        return {
            'avatar': services.choose_private_avatar(passport['information']['gender']),
            'name': passport['profile']['anonymousName']
        }

    def get(self, request, chat_tag):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        info_chattag = mongoDb.chatTag.find_one({'_id': ObjectId(chat_tag)})

        # Query page index get list messages
        start = take * (page_index - 1)
        end = start + take
        list_messages = info_chattag['listMessages'][start:end]
        total_message = info_chattag['totalMessages']

        # Choose avatar and name for list user
        object_avatar_name = {}
        for user_id in info_chattag['listUser']:
            avatar = self.get_avatar_and_name(
                user_id, info_chattag['isPrivate'])
            object_avatar_name[user_id] = avatar

        # Custom response list message
        data_messages = []
        for message in list_messages:
            id = str(message.pop('_id'))

            if message['type'] == enums.message_image:
                for index, value in enumerate(message['content']):
                    message['content'][index] = services.create_link_image(
                        value)

            createdTime = services.get_local_string_date_time(
                message.pop('createdTime'))
            relationship = enums.relationship_self if message[
                'senderId'] == my_id else enums.relationship_not_know

            content = message['content']
            if message['type'] == enums.message_join_community:
                content = object_avatar_name[message['senderId']]['name']
            temp = {
                'id': id,
                'chatTag': chat_tag,
                'type': message['type'],
                'content': content,
                'senderId': message['senderId'],
                'senderAvatar': object_avatar_name[message['senderId']]['avatar'],
                'senderName': object_avatar_name[message['senderId']]['name'],
                'createdTime': createdTime,
                'relationship': relationship,
            }
            data_messages.append(temp)

        # response back
        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_message,
            'data': data_messages
        }

        return Response(res, status=status.HTTP_200_OK)


# New data structure
class GetListMessagesNew(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_avatar_and_name(self, user_id, is_private):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        if not is_private:
            return {
                'avatar': passport['profile']['avatar'],
                'name': passport['profile']['name']
            }

        return {
            'avatar': services.choose_private_avatar(passport['information']['gender']),
            'name': passport['profile']['anonymousName']
        }

    def get(self, request, channel_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        # Get info from "channel_chat" collection
        info_channel = mongoDb.channel_chat.find_one({
            '_id': ObjectId(channel_id)
        })
        object_avatar_name = {}
        for user_id in info_channel['list_user']:
            avatar = self.get_avatar_and_name(
                user_id=user_id,
                is_private=info_channel['is_private']
            )
            object_avatar_name[user_id] = avatar
        total_messages = info_channel['total_messages']

        # Get from "message" collection
        list_messages = mongoDb.message.find(
            {
                'channel_id': channel_id,
                'status': enums.status_active
            }
        ).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)

        data_messages = []
        for message in list_messages:
            id = str(message.pop('_id'))

            if message['type'] == enums.message_image:
                for index, value in enumerate(message['content']):
                    message['content'][index] = services.create_link_image(
                        value)

            createdTime = services.get_local_string_date_time(
                message['created'])

            relationship = enums.relationship_self if message[
                'creator_id'] == my_id else enums.relationship_not_know

            content = message['content']
            if message['type'] == enums.message_join_community:
                content = object_avatar_name[message['creator_id']]['name']

            temp = {
                'id': id,
                'chatTag': channel_id,
                'type': message['type'],
                'content': content,
                'senderId': message['senderId'],
                'senderAvatar': object_avatar_name[message['creator_id']]['avatar'],
                'senderName': object_avatar_name[message['creator_id']]['name'],
                'createdTime': createdTime,
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
