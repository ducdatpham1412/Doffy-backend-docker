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
from django.db.models import Q


class GetProfile(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            return models.Profile.objects.get(user=id)
        except models.Profile.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

    def check_had_been_blocked(self, my_id, your_id):
        try:
            Block.objects.get(Q(block=my_id, blocked=your_id)
                              | Q(block=your_id, blocked=my_id))
            return True
        except Block.DoesNotExist:
            return False

    def check_is_locking_account(self, your_id):
        user_requests = services.get_list_requests_delete_or_block_account(
            user_id=your_id)

        if not user_requests:
            return False

        for request in user_requests:
            if request['type'] == enums.request_user_lock_account:
                return True
            elif request['type'] == enums.request_user_delete_account and request['expired'] > services.get_datetime_now():
                return True

        return False

    def get_relationship(self, my_id, your_id):
        if (my_id == your_id):
            return enums.relationship_self
        try:
            models.Follow.objects.get(follower=my_id, followed=your_id)
            return enums.relationship_following
        except models.Follow.DoesNotExist:
            return enums.relationship_not_following

    def get(self, request, id):
        my_id = services.get_user_id_from_request(request)

        # check had been block or you block them
        if self.check_had_been_blocked(my_id, id) or self.check_is_locking_account(id):
            res = {
                'id': id,
                'relationship': enums.relationship_block
            }
            return Response(res, status=status.HTTP_200_OK)

        # if not, go to get profile
        query = self.get_object(id)
        data_profile = serializers.ProfileSerializer(query).data

        relationship = self.get_relationship(my_id, id)
        res = {
            'id': data_profile['id'],
            'account_type': data_profile['account_type'],
            'name': data_profile['name'],
            'avatar': data_profile['avatar'],
            'cover': data_profile['cover'],
            'description': data_profile['description'],
            'followers': data_profile['followers'],
            'followings': data_profile['followings'],
            'reputations': data_profile['reputations'],
            'location': data_profile['location'],
            'relationship': relationship,
        }

        return Response(res, status=status.HTTP_200_OK)


class EditProfile(GenericAPIView):
    permissions = [IsAuthenticated, ]

    def get_object(self, id):
        try:
            profile = models.Profile.objects.get(user=id)
            return profile
        except models.Profile.DoesNotExist:
            raise CustomError()

    def put(self, request):
        my_id = services.get_user_id_from_request(request)
        request_data = request.data

        my_profile = self.get_object(my_id)

        new_avatar = services.get_object(request_data, 'avatar')
        new_name = services.get_object(request_data, 'name')
        new_description = services.get_object(request_data, 'description')
        new_location = services.get_object(request_data, 'location')

        if new_avatar != None:
            my_profile.avatar = new_avatar
        if new_name != None:
            my_profile.name = new_name
        if new_description != None:
            my_profile.description = new_description
        if new_location != None:
            my_profile.location = new_location

        my_profile.save()

        return Response(None, status=status.HTTP_200_OK)
