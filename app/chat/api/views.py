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
                if passport['setting']['display_avatar']:
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

    def get(self, request):
        id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_chat_tags = mongoDb.chatTag.find(
            {'listUser': id}).sort([('updateTime', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        total_items = mongoDb.chatTag.count_documents({'listUser': id})

        data_list = []

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
                'isStop': get_is_stop(chat_tag['_id']),
                'isBlock': get_is_blocked(chat_tag['listUser']),
                'userSeenMessage': chat_tag['userSeenMessage'],
                'type': chat_tag['type'],
                'color': chat_tag['color'],
                'updateTime': str(chat_tag['updateTime']),
            }

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
                    if passport['setting']['display_avatar']:
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
            if passport['setting']['display_avatar']:
                return passport['profile']['avatar']
            else:
                return services.choose_private_avatar(passport['information']['gender'])

    def get(self, request, chat_tag):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        # query get list messages
        list_messages = mongoDb.message.find(
            {'chatTag': chat_tag}).sort([('createdTime', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
        total_message = mongoDb.message.count_documents({'chatTag': chat_tag})

        # get avatar of list user in chat tag
        info_chattag = mongoDb.chatTag.find_one({'_id': ObjectId(chat_tag)})
        object_sender_avatar = {}
        for user_id in info_chattag['listUser']:
            avatar = self.get_sender_avatar_send_message(
                user_id, info_chattag['isPrivate'])
            object_sender_avatar[user_id] = avatar

        # custom respose list message
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

            temp = {
                'id': user_id,
                'avatar': passport['profile']['avatar'],
                'name': passport['profile']['name'],
                'gender': passport['information']['gender']
            }

            if not display_avatar and not passport['setting']['display_avatar']:
                temp['avatar'] = services.choose_private_avatar(temp['gender'])

            result.append(temp)

        return Response(result, status=status.HTTP_200_OK)


class DeleteMessage(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id_message):
        my_id = services.get_user_id_from_request(request)

        message = mongoDb.message.find_one_and_delete({
            '_id': ObjectId(id_message),
            'senderId': my_id
        })

        if not message:
            raise CustomError(error_message.not_have_permission_delete_message,
                              error_key.not_have_permission_delete_message)
        DisableObject.add_disable_post_or_message(
            enums.disable_message, message)

        return Response(None, status=status.HTTP_200_OK)


# class HandleBubblePlaceForEnjoy(GenericAPIView):
#     def send_bubble_to_palace(self, new_bubble):
#         layer = get_channel_layer()
#         user_active = mongoDb.userActive.find({
#             'userId': {
#                 '$regex': '__'
#             }
#         })

#         for user in user_active:
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['userId']), {
#                 'type': 'send.bubble',
#                 'data': new_bubble
#             })

#     def post(self, request):
#         id = request.data['myId']
#         bubble = request.data['bubble']

#         res = {
#             'id': HandleBubblePalace.save_amount_bubbles_to_mongo(),
#             'name': bubble['name'],
#             'icon': bubble['icon'],
#             'color': bubble['idHobby'],
#             'description': bubble['description'],
#             'creatorId': id,
#             'creatorAvatar': bubble['privateAvatar']
#         }

#         self.send_bubble_to_palace(res)

#         return Response(None, status=status.HTTP_200_OK)


# class RequestPublic(GenericAPIView):
#     permission_classes = [IsAuthenticated, ]

#     def save_request_to_mongo(self, chat_tag):
#         mongoDb.requestPublicChat.find_one_and_update(
#             {
#                 'chatTag': chat_tag
#             },
#             {
#                 '$set': {'listUserAgree': []}
#             },
#             upsert=True
#         )

#     def update_time_chat_tag(self, chat_tag):
#         info_chat_tag = mongoDb.chatTag.find_one_and_update(
#             {
#                 '_id': ObjectId(chat_tag)
#             },
#             {
#                 '$set': {'updateTime': services.get_datetime_now()}
#             }
#         )
#         return info_chat_tag['listUser']

#     def put(self, request, chat_tag):
#         self.save_request_to_mongo(chat_tag)
#         list_user = self.update_time_chat_tag(chat_tag)

#         for user_id in list_user:
#             layer = get_channel_layer()
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user_id), {
#                 'type': 'chat.request_public',
#                 'data': chat_tag
#             })

#         return Response(None, status=status.HTTP_200_OK)


# class AgreeRequestPublic(GenericAPIView):
#     permission_classes = [IsAuthenticated, ]

#     # add user agree to listAgree and check all agree or not
#     def check_all_agree(self, chat_tag, user_agree_id):
#         info_chattag = mongoDb.chatTag.find_one({
#             '_id': ObjectId(chat_tag)
#         })
#         if not info_chattag:
#             return False

#         new_request = mongoDb.requestPublicChat.find_one_and_update(
#             {
#                 'chatTag': chat_tag
#             },
#             {
#                 '$push': {'listUserAgree': user_agree_id}
#             },
#         )
#         if not new_request:
#             return False

#         temp = new_request['listUserAgree']
#         temp.append(user_agree_id)
#         temp.sort()

#         if temp != info_chattag['listUser']:
#             return False

#         return True

#     # if all agree, handle public chat tag
#     def handle_public_chattag(self, chat_tag):
#         update_time = services.get_datetime_now()

#         info_chat_tag = mongoDb.chatTag.find_one_and_update(
#             {
#                 '_id': ObjectId(chat_tag)
#             },
#             {
#                 '$set': {'isPrivate': False, 'updateTime': update_time}
#             }
#         )

#         def get_info_list_member(list_user_id: list) -> list:
#             res = []

#             for user_id in list_user_id:
#                 user = User.objects.get(id=user_id)
#                 passport = GetPassportSerializer(user).data
#                 temp = {
#                     'id': user_id,
#                     'name': passport['profile']['name'],
#                     'avatar': passport['profile']['avatar'],
#                     'gender': passport['information']['gender']
#                 }
#                 res.append(temp)

#             return res

#         update_chat_tag = {
#             'id': str(info_chat_tag.pop('_id')),
#             'listUser': get_info_list_member(info_chat_tag['listUser']),
#             'groupName': info_chat_tag['groupName'],
#             'isPrivate': False,
#             'isStop': False,
#             'isBlock': False,
#             'userSeenMessage': info_chat_tag['userSeenMessage'],
#             'type': info_chat_tag['type'],
#             'updateTime': str(update_time)
#         }

#         # use socket to send update chattag back to front-end
#         for user_id in info_chat_tag['listUser']:
#             layer = get_channel_layer()
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user_id), {
#                 'type': 'chat.agree_public',
#                 'data': update_chat_tag
#             })

#     def put(self, request, chat_tag):
#         id = services.get_user_id_from_request(request)

#         check = self.check_all_agree(chat_tag, id)

#         if check:
#             self.handle_public_chattag(chat_tag)

#         return Response(None, status=status.HTTP_200_OK)


# class HandleMessage(GenericAPIView):
#     permission_classes = [IsAuthenticated, ]

#     def post(self, request):
#         new_message = request.data

#         insert_message = {
#             'chatTag': new_message['chatTag'],
#             'type': new_message['type'],
#             'content': new_message['content'],
#             'senderId': new_message['senderId'],
#             'createdTime': services.get_datetime_now(),
#         }

#         mongoDb.message.insert_one(insert_message)

#         res = {
#             'id': str(insert_message.pop('_id')),
#             **insert_message,
#             'senderAvatar': new_message['senderAvatar'],
#             'createdTime': str(insert_message['createdTime'])
#         }

#         return Response(res, status=status.HTTP_200_OK)


# class HandleChatTag(GenericAPIView):
#     permission_classes = [IsAuthenticated]
#     sender_id = 0
#     is_interact_bubble = False
#     is_message_from_profile = False

#     def get_list_info_user(self, list_user_id: list, display_avatar: bool):
#         result = []

#         for user_id in list_user_id:
#             user = User.objects.get(id=user_id)
#             passport = GetPassportSerializer(user).data

#             temp = {
#                 'id': user_id,
#                 'avatar': passport['profile']['avatar'],
#                 'name': passport['profile']['name'],
#                 'gender': passport['information']['gender']
#             }

#             if not display_avatar and not passport['setting']['display_avatar']:
#                 temp['avatar'] = services.choose_private_avatar(temp['gender'])

#             result.append(temp)

#         return result

#     # handle interact bubble is creating a new chat tag
#     def handle_interact_bubble(self, new_chat_tag):
#         def choose_group_name():
#             if (self.is_interact_bubble):
#                 return new_chat_tag['nameBubble']
#             else:
#                 user1name = list_info_user[0]['name']
#                 user2name = list_info_user[1]['name']
#                 return user1name.split()[0] + " " + user2name.split()[0]

#         list_user_id_sort = new_chat_tag['listUser']
#         list_user_id_sort.sort()

#         list_info_user = self.get_list_info_user(list_user_id_sort, False)
#         group_name = choose_group_name()
#         is_private = self.is_interact_bubble
#         update_time = services.get_datetime_now()
#         user_seen_message = {}
#         for user_id in list_user_id_sort:
#             user_seen_message[str(user_id)] = {
#                 'latestMessage': '',
#                 'isLatest': False,
#             }

#         chat_tag = {
#             'listUser': list_info_user,
#             'groupName': group_name,
#             'isPrivate': is_private,
#             'userSeenMessage': user_seen_message,
#             'updateTime': update_time,
#             'color': new_chat_tag['color']
#         }

#         # save chat tag to mongo
#         # sort listUser to easy handle
#         insert_chat_tag = {
#             'listUser': list_user_id_sort,
#             'groupName': chat_tag['groupName'],
#             'isPrivate': chat_tag['isPrivate'],
#             'isStop': None,
#             'isBlock': None,
#             'userSeenMessage': user_seen_message,
#             'updateTime': chat_tag['updateTime'],
#             'type': new_chat_tag['type'],
#             'color': new_chat_tag['color']
#         }
#         mongoDb.chatTag.insert_one(insert_chat_tag)

#         # save message
#         new_message = {
#             'chatTag': str(insert_chat_tag['_id']),
#             'type': enums.message_text,
#             'content': new_chat_tag['content'],
#             'senderId': self.sender_id,
#             'createdTime': services.get_datetime_now()
#         }
#         mongoDb.message.insert_one(new_message)

#         return {
#             'id': str(insert_chat_tag['_id']),
#             **chat_tag,
#             'updateTime': str(chat_tag['updateTime'])
#         }

#     def handle_message_from_profile(self, new_chat_tag):
#         check = mongoDb.chatTag.find_one_and_update(
#             {
#                 'listUser': {'$all': new_chat_tag['listUser']},
#                 'type': enums.chat_tag_new_from_profile
#             },
#             {
#                 '$set': {'updateTime': services.get_datetime_now()}
#             }
#         )

#         if not check:
#             res = self.handle_interact_bubble(new_chat_tag)
#             return res

#         # save message
#         new_message = {
#             'chatTag': str(check['_id']),
#             'type': enums.message_text,
#             'content': new_chat_tag['content'],
#             'senderId': self.sender_id,
#             'createdTime': services.get_datetime_now()
#         }
#         mongoDb.message.insert_one(new_message)

#         # send chat_tag to all member
#         list_user = self.get_list_info_user(new_chat_tag['listUser'], True)
#         result = {
#             'id': str(check.pop('_id')),
#             'listUser': list_user,
#             'groupName': check['groupName'],
#             'isPrivate': check['isPrivate'],
#             'updateTime': str(check['updateTime']),
#             'type': check['type'],
#             'color': check['color']
#         }

#         return result

#     def send_chat_tag_to_all_member(self, chat_tag_res):
#         layer = get_channel_layer()
#         for user in services.filter_the_same_id(chat_tag_res['listUser']):
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['id']), {
#                 'type': 'chat.tag',
#                 'data': chat_tag_res
#             })

#     def send_delete_bubble_to_all_user_active(self, id_bubble):
#         user_active = mongoDb.userActive.find()
#         # user_active = mongoDb.userActive.find({'userId': {'$ne': '__*'}})
#         layer = get_channel_layer()
#         for user in user_active:
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['userId']), {
#                 'type': 'chat.delete_bubble',
#                 'data': id_bubble
#             })

#     def post(self, request):
#         self.sender_id = services.get_user_id_from_request(request)
#         new_chat_tag = request.data
#         type = new_chat_tag['type']

#         self.is_interact_bubble = type == enums.chat_tag_new_from_bubble
#         self.is_message_from_profile = type == enums.chat_tag_new_from_profile

#         if self.is_interact_bubble:
#             res = self.handle_interact_bubble(new_chat_tag)
#         elif self.is_message_from_profile:
#             res = self.handle_message_from_profile(new_chat_tag)
#         else:
#             res = None

#         # send socket bubble delete to all member
#         if self.is_interact_bubble:
#             self.send_delete_bubble_to_all_user_active(
#                 new_chat_tag['idBubble'])

#         # send socket new / update chat tag to member in chat tag
#         self.send_chat_tag_to_all_member(res)

#         return Response(None, status=status.HTTP_200_OK)


# class HandleChatTagEnjoy(GenericAPIView):
#     sender_id = 0

#     def get_list_info_user(self, list_user_id: list):
#         result = []

#         for user_id in list_user_id:
#             temp = {
#                 'id': user_id,
#                 'avatar': services.choose_private_avatar(enums.gender_female),
#                 'name': enums.NAME_DEFAULT,
#                 'gender': enums.gender_female
#             }
#             result.append(temp)

#         return result

#     def handle_interact_bubble(self, new_chat_tag):
#         list_user_id_sort = new_chat_tag['listUser']
#         list_user_id_sort.sort()

#         list_info_user = self.get_list_info_user(list_user_id_sort)
#         group_name = new_chat_tag['nameBubble']
#         is_private = True
#         update_time = services.get_datetime_now()
#         user_seen_message = {}
#         for user_id in list_user_id_sort:
#             user_seen_message[str(user_id)] = {
#                 'latestMessage': '',
#                 'isLatest': False
#             }

#         chat_tag = {
#             'id': str(ObjectId()),
#             'listUser': list_info_user,
#             'groupName': group_name,
#             'isPrivate': is_private,
#             'userSeenMessage': user_seen_message,
#             'updateTime': str(update_time),
#             'color': new_chat_tag['color']
#         }

#         message = {
#             'id': str(ObjectId()),
#             'chatTag': chat_tag['id'],
#             'type': enums.message_text,
#             'content': new_chat_tag['content'],
#             'senderId': self.sender_id,
#             'senderAvatar': services.create_link_image(enums.PRIVATE_AVATAR['girl']),
#             'createdTime': str(update_time)
#         }

#         return {
#             'new_chat_tag': chat_tag,
#             'new_message': message
#         }

#     def send_chat_tag_and_message_to_all_member(self, res):
#         layer = get_channel_layer()

#         chat_tag_res = res['new_chat_tag']
#         message_res = res['new_message']

#         for user in services.filter_the_same_id(chat_tag_res['listUser']):
#             if message_res['senderId'] == user['id']:
#                 relationship = enums.relationship_self
#             else:
#                 relationship = enums.relationship_not_know

#             new_message = {
#                 **message_res,
#                 'relationship': relationship
#             }

#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['id']), {
#                 'type': 'chat.tag',
#                 'data': {
#                     'newChatTag': chat_tag_res,
#                     'newMessage': new_message
#                 }
#             })

#     def send_delete_bubble_to_all_user_active(self, id_bubble):
#         user_active = mongoDb.userActive.find({'userId': {'$regex': '__*'}})
#         layer = get_channel_layer()
#         for user in user_active:
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['userId']), {
#                 'type': 'chat.delete_bubble',
#                 'data': id_bubble
#             })

#     def post(self, request):
#         self.sender_id = request.data['myId']
#         new_chat_tag = request.data['newChatTag']

#         res = self.handle_interact_bubble(new_chat_tag)
#         self.send_chat_tag_and_message_to_all_member(res)
#         self.send_delete_bubble_to_all_user_active(new_chat_tag['idBubble'])

#         return Response(None, status=status.HTTP_200_OK)


# class HandleBubblePalace(GenericAPIView):
#     permission_classes = [IsAuthenticated]

#     @staticmethod
#     def save_amount_bubbles_to_mongo():
#         temp = mongoDb.numberBubbles.find_one_and_update(
#             {},
#             {
#                 '$inc': {'number': 1}
#             }
#         )
#         return temp['number'] + 1

#     def send_bubble_to_palace(self, new_bubble):
#         layer = get_channel_layer()
#         user_active = mongoDb.userActive.find()

#         for user in user_active:
#             async_to_sync(layer.group_send)(services.create_socket_bubble_chattag(user['userId']), {
#                 'type': 'send.bubble',
#                 'data': new_bubble
#             })

#     def post(self, request):
#         id = services.get_user_id_from_request(request)
#         bubble = request.data

#         res = {
#             'id': self.save_amount_bubbles_to_mongo(),
#             'name': bubble['name'],
#             'icon': bubble['icon'],
#             'color': bubble['idHobby'],
#             'description': bubble['description'],
#             'creatorId': id,
#             'creatorAvatar': bubble['privateAvatar']
#         }

#         self.send_bubble_to_palace(res)

#         return Response(None, status=status.HTTP_200_OK)
