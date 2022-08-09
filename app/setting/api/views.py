from authentication.serializers import UserSerializer
from authentication.models import User
from django.shortcuts import render
from findme.mongo import mongoDb
from myprofile.serializers import ProfileSerializer
from myprofile.models import Follow, Profile
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting import models
from setting.api.serializers import (ChangeInformationSerializer,
                                     ExtendSerializer, ListBlockSerializer)
from utilities import services, enums
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from utilities.validate import validate_password
from bson import ObjectId
from django.contrib.auth.hashers import make_password, check_password
import requests
import json


class ChangePassword(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_object(self, id, old_password):
        try:
            user = User.objects.get(id=id)

            check = check_password(old_password, user.password)
            if not check:
                raise CustomError(
                    error_message.old_password_not_true, error_key.old_password_not_true)

            return user
        except User.DoesNotExist:
            raise CustomError(error_message.old_password_not_true,
                              error_key.old_password_not_true)

    def put(self, request):
        id = services.get_user_id_from_request(request)

        old_password = request.data['oldPassword']
        newPassword = request.data['newPassword']
        confirmPassword = request.data['confirmPassword']

        # validate
        if not validate_password(newPassword):
            raise CustomError(error_message.password_invalid,
                              error_key.password_invalid)
        if confirmPassword != newPassword:
            raise CustomError(error_message.password_not_match,
                              error_key.password_not_match)

        # change
        user = self.get_object(id, old_password)
        user.password = make_password(newPassword)
        user.save()

        return Response(None, status=status.HTTP_200_OK)


class ChangeTheme(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtendSerializer

    def get_object(self, id):
        try:
            extend = models.Extend.objects.get(user=id)
            return extend
        except models.Extend.DoesNotExist:
            raise CustomError()

    def put(self, request):
        id = services.get_user_id_from_request(request)
        new_theme = request.data['newTheme']

        data = {
            'theme': new_theme
        }
        extend = self.get_object(id)

        serializer = self.serializer_class(extend, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(None, status=status.HTTP_200_OK)


class ChangeLanguage(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtendSerializer

    def put(self, request):
        id = services.get_user_id_from_request(request)
        new_language = request.data['newLanguage']

        data = {
            'language': new_language
        }

        try:
            extend = models.Extend.objects.get(user=id)
            serializer = self.serializer_class(extend, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        except models.Extend.DoesNotExist:
            raise CustomError()


class ChangeDisplayAvatar(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtendSerializer

    def put(self, request):
        id = services.get_user_id_from_request(request)
        new_value = request.data['value']

        data = {
            'display_avatar': new_value
        }

        try:
            extend = models.Extend.objects.get(user=id)
            serializer = self.serializer_class(extend, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        except models.Extend.DoesNotExist:
            raise CustomError()


class ChangeInformation(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        id = services.get_user_id_from_request(request)
        new_information = request.data

        # update in information
        information = models.Information.objects.get(user=id)
        serializer = ChangeInformationSerializer(
            information, data=new_information)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # update in authentication user
        user = User.objects.get(id=id)
        user_serializer = UserSerializer(user, data=new_information)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        # update name in profile
        profile = Profile.objects.get(user=id)
        profile_serializer = ProfileSerializer(profile, data=new_information)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response(None, status=status.HTTP_200_OK)


class BlockUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            user = User.objects.get(id=id)
            return user
        except User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

    def check_not_blocked(self, my_id, your_id):
        try:
            models.Block.objects.get(block=my_id, blocked=your_id)
            raise CustomError(error_message.you_have_blocked_this_person,
                              error_key.you_have_blocked_this_person)
        except models.Block.DoesNotExist:
            return

    def un_follow_if_following(self, my_id, your_id):
        try:
            follow = Follow.objects.get(follower=my_id, followed=your_id)
            follow.delete()
        except Follow.DoesNotExist:
            try:
                follow = Follow.objects.get(follower=your_id, followed=my_id)
                follow.delete()
            except Follow.DoesNotExist:
                return

    def send_socket_block(self, my_id, your_id):
        list_user_id_sort = [my_id, your_id]
        list_user_id_sort.sort()
        conversation = mongoDb.chat_conversation.find_one({
            'list_users': list_user_id_sort
        })
        conversation_id = services.get_object(conversation, '_id')
        if conversation_id:
            requests.post('http://chat:1412/setting/block', data=json.dumps({
                'conversationId': str(conversation_id),
            }))

    def post(self, request, id):
        my_id = services.get_user_id_from_request(request)

        if my_id == id:
            raise CustomError()

        self.check_not_blocked(my_id, id)
        self.un_follow_if_following(my_id, id)

        my_profile = self.get_object(my_id)
        your_profile = self.get_object(id)
        temp = models.Block(block=my_profile, blocked=your_profile)
        temp.save()

        self.send_socket_block(my_id=my_id, your_id=id)

        return Response(None, status=status.HTTP_200_OK)


class UnblockUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, my_id, your_id):
        try:
            block = models.Block.objects.get(block=my_id, blocked=your_id)
            return block
        except models.Block.DoesNotExist:
            raise CustomError(error_message.you_not_block_this_person,
                              error_key.you_not_block_this_person)

    def open_conversation(self, my_id, your_id):
        list_user_id_sort = [my_id, your_id]
        list_user_id_sort.sort()
        conversation = mongoDb.chat_conversation.find_one({
            'list_users': list_user_id_sort
        })
        conversation_id = services.get_object(conversation, '_id')
        if conversation_id:
            requests.post('http://chat:1412/setting/unblock', data=json.dumps({
                'conversationId': str(conversation_id),
            }))

    def post(self, request, id):
        my_id = services.get_user_id_from_request(request)

        block = self.get_object(my_id, id)
        block.delete()

        self.open_conversation(my_id, id)

        return Response(None, status=status.HTTP_200_OK)


class StopConversation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id': ObjectId(conversation_id),
                'list_users': my_id,
            },
            {
                '$set': {
                    'status': enums.status_conversation_stop
                }
            }
        )

        if not conversation:
            raise CustomError(error_message.conversation_not_existed,
                              error_key.conversation_not_existed)
        else:
            requests.post('http://chat:1412/setting/stop-conversation', json.dumps({
                'conversationId': conversation_id,
            }))

        return Response(None, status=status.HTTP_200_OK)


class OpenConversation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, conversation_id):
        my_id = services.get_user_id_from_request(request)

        conversation = mongoDb.chat_conversation.find_one_and_update(
            {
                '_id':  ObjectId(conversation_id),
                'list_users': my_id
            },
            {
                '$set': {
                    'status': enums.status_conversation_active
                }
            }
        )
        if not conversation:
            raise CustomError(error_message.conversation_not_existed,
                              error_key.conversation_not_existed)
        else:
            requests.post('http://chat:1412/setting/open-conversation', json.dumps({
                'conversationId': conversation_id,
            }))

        return Response(None, status=status.HTTP_200_OK)


class GetListBlock(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListBlockSerializer

    def get(self, request):
        id = services.get_user_id_from_request(request)

        list_block = models.Block.objects.filter(block=id)
        serializer = self.serializer_class(list_block, many=True)

        res = []
        for item in serializer.data:
            profile = Profile.objects.get(user=item['blocked'])
            data_profile = ProfileSerializer(profile).data
            temp = {
                'id': item['id'],
                'profile': {
                    'id': data_profile['id'],
                    'avatar': data_profile['avatar'],
                    'name': data_profile['name']
                }
            }
            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)


class PrivacyPolicy(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/privacy_policy.html')


class TermsOfUse(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/term_of_use.html')


class DoffySupport(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/doffy_support.html')


class UserGuide(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/user_guide.html')


class LandingPage(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/landing_page.html')


class LinhNgao(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/linh_ngao.html')
