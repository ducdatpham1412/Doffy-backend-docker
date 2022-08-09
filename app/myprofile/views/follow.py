import json
from authentication.models import User
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from myprofile import models
from myprofile import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting.models import Block
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
import requests


class FollowUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            user = User.objects.get(id=id)
            return user
        except User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

    def check_had_follow(self, my_id, your_id):
        try:
            models.Follow.objects.get(follower=my_id, followed=your_id)
            return True
        except models.Follow.DoesNotExist:
            return False

    def check_had_blocked(self, my_id, your_id):
        try:
            Block.objects.get(block=my_id, blocked=your_id)
            return True
        except Block.DoesNotExist:
            try:
                Block.objects.get(block=your_id, blocked=my_id)
                return True
            except Block.DoesNotExist:
                return False

    def put(self, request, id):
        my_id = services.get_user_id_from_request(request)

        if self.check_had_blocked(my_id, id):
            raise CustomError()

        if not self.check_had_follow(my_id, id):
            my_profile = self.get_object(my_id)
            your_profile = self.get_object(id)

            follow = models.Follow(follower=my_profile,
                                   followed=your_profile)
            follow.save()

            # Get my name
            profile = models.Profile.objects.get(user=my_id)
            services.send_notification({
                'contents': {
                    'vi': '{} bắt đầu theo dõi bạn'.format(profile.name),
                    'en': '{} start following you'.format(profile.name),
                },
                'filters': [
                    {
                        'field': 'tag',
                        'key': 'userId',
                        'relation': '=',
                        'value': id
                    }
                ],
                'data': {
                    'type': enums.notification_follow
                }
            })

            # Send socket notification
            data_notification = {
                'id': str(ObjectId()),
                'type': enums.notification_follow,
                'content': '{} đã bắt đầu theo dõi bạn'.format(profile.name),
                'image': services.create_link_image(profile.avatar),
                'creatorId': my_id,
                'hadRead': False,
            }

            mongoDb.notification.find_one_and_update(
                {
                    'userId': id
                },
                {
                    '$push': {
                        'list': {
                            '$each': [data_notification],
                            '$position': 0
                        }
                    }
                }
            )

            requests.post('http://chat:1412/notification/follow', data=json.dumps({
                'receiver': id,
                'data': data_notification,
            }))

            return Response(None, status=status.HTTP_200_OK)

        else:
            raise CustomError(error_message.your_have_follow_this_person,
                              error_key.your_have_follow_this_person)


class UnFollowUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, my_id, your_id):
        try:
            follow = models.Follow.objects.get(
                follower=my_id, followed=your_id)
            return follow
        except models.Follow.DoesNotExist:
            raise CustomError()

    def check_had_blocked(self, my_id, your_id):
        try:
            Block.objects.get(block=my_id, blocked=your_id)
            return True
        except Block.DoesNotExist:
            try:
                Block.objects.get(block=your_id, blocked=my_id)
                return True
            except Block.DoesNotExist:
                return False

    def un_follow_user(self, my_id, your_id):
        if not self.check_had_blocked(my_id, your_id):
            follow = self.get_object(my_id, your_id)
            follow.delete()
            return Response(None, status=status.HTTP_200_OK)
        else:
            raise CustomError()

    def put(self, request, id):
        my_id = services.get_user_id_from_request(request)

        return self.un_follow_user(my_id, id)


class GetListFollow(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    my_id = None
    is_get_follower = False
    is_get_list_of_me = False

    def get_relationship_follower(self, your_id):
        # your self
        if (your_id == self.my_id):
            return enums.relationship_self

        # get list following of me -> not need to check
        if not self.is_get_follower and self.is_get_list_of_me:
            return enums.relationship_not_know

        # only check when get list follower
        try:
            models.Follow.objects.get(followed=your_id, follower=self.my_id)
            return enums.relationship_following
        except models.Follow.DoesNotExist:
            return enums.relationship_not_following

    def get_info_user(self, list_id):
        res = []
        for id in list_id:
            profile = models.Profile.objects.get(user=id)
            avatar = services.create_link_image(profile.avatar)
            temp = {
                'id': id,
                'name': profile.name,
                'avatar': avatar,
                'description': profile.description,
                'relationship': self.get_relationship_follower(id)
            }
            res.append(temp)

        return res

    def get(self, request, user_id):
        self.my_id = services.get_user_id_from_request(request)
        self.is_get_list_of_me = self.my_id == user_id

        type_follow = int(request.query_params['typeFollow'][0])
        page_index = int(request.query_params['pageIndex'])
        take = int(request.query_params['take'])

        start = int((page_index-1) * take)
        end = int(page_index * take)

        # get list my followers
        if type_follow == enums.follow_follower:
            self.is_get_follower = True
            query = models.Follow.objects.filter(followed=user_id)[start:end]
            data_follower = serializers.FollowSerializer(query, many=True).data

            list_id = []
            for follower in data_follower:
                list_id.append(follower['follower'])

            return Response(self.get_info_user(list_id), status=status.HTTP_200_OK)

        # get list my followings
        elif type_follow == enums.follow_following:
            query = models.Follow.objects.filter(follower=user_id)[start:end]
            data_following = serializers.FollowSerializer(
                query, many=True).data

            list_id = []
            for following in data_following:
                list_id.append(following['followed'])

            return Response(self.get_info_user(list_id), status=status.HTTP_200_OK)

        else:
            raise CustomError()
