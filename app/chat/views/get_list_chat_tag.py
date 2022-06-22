import pymongo
from authentication.models import User
from common.api.serializers import GetPassportSerializer
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting.models import Block
from utilities import enums, services
from utilities.renderers import PagingRenderer


class GetListChatTags(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_info_of_member(self, user_id, is_chattag_private):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        def get_avatar():
            if not is_chattag_private:
                return passport['profile']['avatar']
            else:
                return services.choose_private_avatar(passport['information']['gender'])

        name = passport['profile']['anonymousName'] if is_chattag_private else passport['profile']['name']
        avatar = get_avatar()
        gender = passport['information']['gender']

        return {
            'id': user_id,
            'name': name,
            'avatar': avatar,
            'gender': gender
        }

    def get(self, request):
        id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_chat_tags = mongoDb.chatTag.find(
            {'listUser': id}).sort([('updateTime', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        total_items = mongoDb.chatTag.count_documents({'listUser': id})

        data_list = []

        def get_is_blocked(type: int, list_user: list):
            """
            If is chat tag group, return False
            """
            if type == enums.chat_tag_group:
                return False

            """
            Chat tag couple
            """
            your_id = None
            for user_id in list_user:
                if (user_id != id):
                    your_id = user_id

            # This is chattag of me
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

        for chat_tag in list_chat_tags:
            infoListUser = []
            for user_id in chat_tag['listUser']:
                infoListUser.append(self.get_info_of_member(
                    user_id, chat_tag['isPrivate']))

            temp = {
                'id': str(chat_tag['_id']),
                'listUser': infoListUser,
                'groupName': chat_tag['groupName'],
                'isPrivate': chat_tag['isPrivate'],
                'isStop': get_is_stop(str(chat_tag['_id'])),
                'isBlock': get_is_blocked(chat_tag['type'], chat_tag['listUser']),
                'userSeenMessage': chat_tag['userSeenMessage'],
                'type': chat_tag['type'],
                'color': chat_tag['color'],
                'updateTime': str(chat_tag['updateTime']),
            }

            if chat_tag['type'] == enums.chat_tag_group:
                temp['image'] = services.create_link_image(chat_tag['image'])

            data_list.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_items,
            'data': data_list
        }

        return Response(res, status=status.HTTP_200_OK)


class GetListChannelChat(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_info_of_member(self, user_id: int, is_channel_private: bool):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        avatar = services.choose_private_avatar(
            passport['information']['gender']) if is_channel_private else passport['profile']['avatar']
        name = passport['profile']['anonymousName'] if is_channel_private else passport['profile']['name']
        gender = passport['information']['gender']

        return {
            'id': user_id,
            'name': name,
            'avatar': avatar,
            'gender': gender,
        }

    def get(self, request):
        id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_channel_chat = mongoDb.channel_chat.find(
            {'listUser': id}).sort([('modified', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        total_items = mongoDb.channel_chat.count_documents({'listUser': id})

        data_response = []

        def get_is_stop(channel_id):
            check_stop = mongoDb.chatTagStopped.find_one({
                'chatTag': channel_id,
                'isActive': True
            })
            if not check_stop:
                return False
            return True

        def get_is_blocked(type: int, list_user: list):
            if type == enums.chat_tag_group:
                return False

            # Channel couple
            friend_id = None
            for user_id in list_user:
                if (user_id != id):
                    friend_id = user_id
            # channel of me
            if friend_id == None:
                return False

            try:
                Block.objects.get(block=id, blocked=friend_id)
            except Block.DoesNotExist:
                try:
                    Block.objects.get(block=friend_id, blocked=id)
                except Block.DoesNotExist:
                    return False

        for channel in list_channel_chat:
            info_list_user = []
            for user_id in channel['listUser']:
                info_list_user.append(self.get_info_of_member(
                    user_id=user_id, is_channel_private=channel['is_private']))

            temp = {
                'id': str(channel['_id']),
                'listUser': info_list_user,
                'groupName': channel['channel_name'],
                'isPrivate': channel['is_private'],
                'isStop': get_is_stop(str(channel['_id'])),
                'isBlock': get_is_blocked(channel['type'], channel['list_user']),
                'type': channel['type'],
                'color': channel['color'],
                'updateTime': str(channel['modified'])
            }
            if channel['type'] == enums.chat_tag_group:
                temp['image'] = services.create_link_image(channel['image'])

            data_response.append(temp)

        # Response
        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_items,
            'data': data_response
        }

        return Response(res, status=status.HTTP_200_OK)
