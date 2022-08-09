import json
from common.serializers import GetPassportSerializer
from authentication.models import User
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from utilities.disableObject import DisableObject
import requests


class CreateGroup(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_my_information(self, my_id):
        user = User.objects.get(id=my_id)
        passport = GetPassportSerializer(user).data
        return {
            'id': my_id,
            'name': passport['profile']['anonymousName'],
            'avatar': passport['profile']['avatar'],
            'gender': passport['information']['gender']
        }

    def post(self, request):
        my_id = services.get_user_id_from_request(request)

        content = request.data['content']
        images = request.data['images']
        color = request.data['color']
        name = request.data['name']

        # Create chat tag
        insert_chat_tag = {
            'listUser': [my_id],
            'groupName': name,
            'image': images[0],
            'isPrivate': True,
            'userSeenMessage': {
                '{}'.format(my_id): {
                    'latestMessage': "",
                    'isLatest': False
                }
            },
            'createdTime': services.get_datetime_now(),
            'updateTime': services.get_datetime_now(),
            'type': enums.chat_tag_group,
            'color': color,
            'listMessages': [],
            'totalMessages': 0,
        }
        mongoDb.chatTag.insert_one(insert_chat_tag)

        # Create post
        insert_post_group = {
            'content': content,
            'images': images,
            'chatTagId': str(insert_chat_tag['_id']),
            'creatorId': my_id,
            'createdTime': services.get_datetime_now(),
            'color': color,
            'name': name,
            'listMembers': [my_id, ]
        }
        mongoDb.profilePostGroup.insert_one(insert_post_group)

        res_images = []
        for img in insert_post_group['images']:
            res_images.append(services.create_link_image(img))
        res = {
            'id': str(insert_post_group['_id']),
            'content': content,
            'images': res_images,
            'chatTagId': insert_post_group['chatTagId'],
            'creatorId': my_id,
            'createdTime': str(insert_post_group['createdTime']),
            'color': color,
            'name': name,
            'listMembers': insert_post_group['listMembers']
        }

        # Send to socket server to join room
        data_socket = {
            'id': str(insert_chat_tag.pop('_id')),
            **insert_chat_tag,
            'listUser': [self.get_my_information(my_id)],
            'image': res_images[0],
            'createdTime': res['createdTime'],
            'updateTime': res['createdTime']
        }

        requests.post('http://chat:1412/new-chat-tag', data=json.dumps({
            'receiver': my_id,
            'data': data_socket
        }))

        return Response(res, status=status.HTTP_200_OK)


class GetMyListGroups(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)

        list_my_groups = mongoDb.profilePostGroup.find({
            'creatorId': my_id
        })

        res = []

        for group in list_my_groups:
            res_images = []
            for image in group['images']:
                res_images.append(services.create_link_image(image))
            temp = {
                'id': str(group['_id']),
                'content': group['content'],
                'images': res_images,
                'chatTagId': group['chatTagId'],
                'creatorId': group['creatorId'],
                'createdTime': str(group['createdTime']),
                'color': group['color'],
                'name': group['name'],
                'relationship': enums.relationship_self
            }

            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)


class EditGroup(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, group_id):
        my_id = services.get_user_id_from_request(request)

        bubble = mongoDb.profilePostGroup.find_one_and_update(
            {
                '_id': ObjectId(group_id),
                'creatorId': my_id
            },
            {
                '$set': request.data
            }
        )

        if not bubble:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


class DeleteGroup(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, group_id):
        my_id = services.get_user_id_from_request(request)

        group = mongoDb.profilePostGroup.find_one_and_delete({
            '_id': ObjectId(group_id),
            'creatorId': my_id
        })

        if not group:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)
        DisableObject.add_disable_post_or_message(
            enums.disable_profile_post, group)

        return Response(None, status=status.HTTP_200_OK)
