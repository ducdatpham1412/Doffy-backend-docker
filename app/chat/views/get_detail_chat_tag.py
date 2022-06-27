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


class GetDetailChatTag(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, chat_tag_id):
        id = services.get_user_id_from_request(request)

        def get_info_of_member(user_id, is_chattag_private):
            user = User.objects.get(id=user_id)
            passport = GetPassportSerializer(user).data

            def get_avatar():
                if not is_chattag_private:
                    return passport['profile']['avatar']
                else:
                    return services.choose_private_avatar(passport['information']['gender'])

            name = '' if is_chattag_private else passport['profile']['name']
            avatar = get_avatar()
            gender = passport['information']['gender']

            return {
                'id': user_id,
                'name': name,
                'avatar': avatar,
                'gender': gender
            }

        def get_is_blocked(list_user: list):
            your_id = None
            for user_id in list_user:
                if (user_id != id):
                    your_id = user_id

            # is me
            if your_id == None:
                return False

            try:
                Block.objects.get(block=id, blocked=your_id)
            except Block.DoesNotExist:
                try:
                    Block.objects.get(block=your_id, blocked=id)
                except Block.DoesNotExist:
                    return False

            return True

        def get_is_stop(chat_tag_id):
            check_stop = mongoDb.chatTagStopped.find_one({
                'chatTag': chat_tag_id,
                'isActive': True
            })
            if not check_stop:
                return False
            return True

        chat_tag = mongoDb.chatTag.find_one({
            '_id': ObjectId(chat_tag_id)
        })

        infoListUser = []
        for user_id in chat_tag['listUser']:
            infoListUser.append(get_info_of_member(
                user_id, chat_tag['isPrivate']))
        res = {
            'id': str(chat_tag['_id']),
            'listUser': infoListUser,
            'groupName': chat_tag['groupName'],
            'isPrivate': chat_tag['isPrivate'],
            'isStop': get_is_stop(chat_tag['_id']),
            'isBlock': get_is_blocked(chat_tag['listUser']),
            'userSeenMessage': chat_tag['userSeenMessage'],
            'type': chat_tag['type'],
            'color': chat_tag['color'],
            'updateTime': str(chat_tag['updateTime']),
        }
        if chat_tag['type'] == enums.chat_tag_group:
            res['image'] = services.create_link_image(chat_tag['image'])

        return Response(res, status=status.HTTP_200_OK)


"""
New structure
"""


class GetDetailChannel(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_info_of_member(self, user_id, is_private):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        name = '' if is_private else passport['profile']['name']
        gender = passport['information']['gender']
        avatar = services.choose_private_avatar(
            gender) if is_private else passport['profile']['avatar']

        return {
            'id': user_id,
            'name': name,
            'avatar': avatar,
            'gender': gender
        }

    def get(self, request, channel_id):
        my_id = services.get_user_id_from_request(request)

        def get_is_blocked(type: int, list_user: list):
            if type == enums.chat_tag_group:
                return False

            # Channel couple
            friend_id = None
            for user_id in list_user:
                if user_id != my_id:
                    friend_id = user_id

            if friend_id == None:
                return False

            try:
                Block.objects.get(block=my_id, blocked=friend_id)
            except Block.DoesNotExist:
                try:
                    Block.objects.get(block=friend_id, blocked=my_id)
                except Block.DoesNotExist:
                    return False

            return True

        channel = mongoDb.channel_chat.find_one({
            '_id': ObjectId(channel_id)
        })

        info_list_user = []
        for user_id in channel['list_user']:
            info = self.get_info_of_member(
                user_id=user_id, is_private=channel['is_private'])
            info_list_user.append(info)

        is_channel_stop = None
        if channel['type'] == enums.chat_tag_group:
            is_channel_stop = False
        else:
            is_channel_stop = channel['status'] == 2

        res = {
            'id': str(channel['_id']),
            'listUser': info_list_user,
            'groupName': channel['channel_name'],
            'isPrivate': channel['is_private'],
            'isStop': is_channel_stop,
            'isBlock': get_is_blocked(channel['list_user']),
            'type': channel['type'],
            'color': channel['color'],
            'updateTime': str(channel['modified'])
        }
        if channel['type'] == enums.chat_tag_group:
            res['image'] = services.create_link_image(channel['image'])

        return Response(res, status=status.HTTP_200_OK)
