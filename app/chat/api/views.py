import pymongo
from authentication.models import User
from bson.objectid import ObjectId
from common.api.serializers import GetPassportSerializer
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from utilities.renderers import PagingRenderer
from setting.models import Block
from utilities.disableObject import DisableObject


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
            If is chattag group, return False
            """
            if type == enums.chat_tag_group:
                return False

            """
            Chattag couple
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


class GetListMessages(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_sender_avatar_send_message(self, user_id, is_chattag_private):
        user = User.objects.get(id=user_id)
        passport = GetPassportSerializer(user).data

        if not is_chattag_private:
            return passport['profile']['avatar']
        else:
            return services.choose_private_avatar(passport['information']['gender'])

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

        # Choose avatar for list user in chat tag
        object_sender_avatar = {}
        for user_id in info_chattag['listUser']:
            avatar = self.get_sender_avatar_send_message(
                user_id, info_chattag['isPrivate'])
            object_sender_avatar[user_id] = avatar

        # Custom respose list message
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

            temp = {
                'id': id,
                'chatTag': chat_tag,
                'type': message['type'],
                'content': message['content'],
                'senderId': message['senderId'],
                'senderAvatar': object_sender_avatar[message['senderId']],
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


class ChangeGroupNameChatTag(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag):
        myId = services.get_user_id_from_request(request)
        new_name = request.data['name']
        chat_tag_id = ObjectId(chat_tag)

        mongoDb.chatTag.find_one_and_update(
            {
                '_id': chat_tag_id,
                'listUser': myId
            },
            {
                '$set': {
                    'groupName': new_name,
                    'updateTime': services.get_datetime_now()
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)


class GetListUserInfo(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def post(self, request):
        list_user_id = request.data['listUserId']
        display_avatar = request.data['displayAvatar']

        result = []

        for user_id in list_user_id:
            user = User.objects.get(id=user_id)
            passport = GetPassportSerializer(user).data

            avatar = passport['profile']['avatar'] if display_avatar else services.choose_private_avatar(
                passport['information']['gender'])

            temp = {
                'id': user_id,
                'avatar': avatar,
                'name': passport['profile']['name'],
                'gender': passport['information']['gender']
            }

            result.append(temp)

        return Response(result, status=status.HTTP_200_OK)


class DeleteMessage(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        chat_tag_id = request.data['chatTagId']
        message_id = request.data['messageId']
        my_id = services.get_user_id_from_request(request)

        info_chat_tag = mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(chat_tag_id)
            },
            {
                '$pull': {
                    'listMessages': {
                        '_id': ObjectId(message_id),
                        'senderId': my_id,
                    }
                },
                '$inc': {
                    'totalMessages': -1
                }
            }
        )

        # Check can delete or not and Add to Disable object
        if not info_chat_tag:
            raise CustomError()
        check_index = -1
        for index, value in enumerate(info_chat_tag['listMessages']):
            if value['_id'] == ObjectId(message_id) and value['senderId'] == my_id:
                check_index = index
                DisableObject.add_disable_post_or_message(
                    enums.disable_message, value)
                break
        if (check_index == -1):
            raise CustomError(error_message.not_have_permission_delete_message,
                              error_key.not_have_permission_delete_message)

        # Response
        return Response(None, status=status.HTTP_200_OK)


class ChangeChatColor(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag):
        my_id = services.get_user_id_from_request(request)
        new_color = request.data['color']

        mongoDb.chatTag.find_one_and_update(
            {
                '_id': ObjectId(chat_tag),
                'listUser': my_id
            },
            {
                '$set': {
                    'color': new_color,
                    'updateTime': services.get_datetime_now()
                }
            }
        )

        return Response(None, status=status.HTTP_200_OK)
