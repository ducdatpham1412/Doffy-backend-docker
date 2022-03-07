from asgiref.sync import async_to_sync
from authentication.api.serializers import UserSerializer
from authentication.models import User
from channels.layers import get_channel_layer
from django.shortcuts import render
from findme.mongo import mongoDb
from myprofile.api.serializers import ProfileSerializer
from myprofile.models import Follow, Profile
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting import models
from setting.api.serializers import (ChangeInformationSerializer,
                                     ExtendSerializer, ListBlockSerializer)
from utilities import services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from utilities.validate import validate_password
from bson import ObjectId
from django.contrib.auth.hashers import make_password, check_password


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

    def get_list_chat_tag_blocked(self, my_id, your_id):
        list_user_id_sort = [my_id, your_id]
        list_user_id_sort.sort()

        list_chat_tag = mongoDb.chatTag.find({
            'listUser': list_user_id_sort
        })

        list_chat_tag_id_blocked = []
        for chat_tag in list_chat_tag:
            list_chat_tag_id_blocked.append(str(chat_tag['_id']))

        return list_chat_tag_id_blocked

    def post(self, request, id):
        my_id = services.get_user_id_from_request(request)

        # your self
        if my_id == id:
            raise CustomError()

        self.check_not_blocked(my_id, id)
        self.un_follow_if_following(my_id, id)

        my_profile = self.get_object(my_id)
        your_profile = self.get_object(id)
        temp = models.Block(block=my_profile, blocked=your_profile)
        temp.save()

        res = self.get_list_chat_tag_blocked(my_id, id)

        return Response(res, status=status.HTTP_200_OK)


class UnblockUser(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, my_id, your_id):
        try:
            block = models.Block.objects.get(block=my_id, blocked=your_id)
            return block
        except models.Block.DoesNotExist:
            raise CustomError(error_message.you_not_block_this_person,
                              error_key.you_not_block_this_person)

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

    def open_all_chat_tags(self, my_id, your_id):
        list_user_id_sort = [my_id, your_id]
        list_user_id_sort.sort()

        list_chat_tag_opened = []

        list_chat_tag = mongoDb.chatTag.find({'listUser': list_user_id_sort})
        for chat_tag in list_chat_tag:
            list_chat_tag_opened.append(str(chat_tag['_id']))

        return list_chat_tag_opened

    def post(self, request, id):
        my_id = services.get_user_id_from_request(request)

        block = self.get_object(my_id, id)
        block.delete()

        res = self.open_all_chat_tags(my_id, id)

        return Response(res, status=status.HTTP_200_OK)


class StopConversation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag_id):
        my_id = services.get_user_id_from_request(request)

        chat_tag = mongoDb.chatTag.find_one({'_id': ObjectId(chat_tag_id)})
        # you self
        your_id = None
        for user_id in chat_tag['listUser']:
            if user_id != my_id:
                your_id = user_id
        if not your_id:
            raise CustomError()

        # insert chat tag stop
        mongoDb.chatTagStopped.insert_one({
            'chatTag': ObjectId(chat_tag_id),
            'userStop': my_id,
            'isActive': True,
        })

        return Response(None, status=status.HTTP_200_OK)


class OpenConversation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, chat_tag_id):
        my_id = services.get_user_id_from_request(request)

        # set in chatTagStopped
        check_stop_chat = mongoDb.chatTagStopped.find_one_and_update(
            {
                'chatTag': ObjectId(chat_tag_id),
                'userStop': my_id
            },
            {
                '$set': {
                    'isActive': False
                }
            }
        )
        if not check_stop_chat:
            raise CustomError(error_message.you_can_not_open_this_conversation,
                              error_key.you_can_not_open_this_conversation)

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


class LinhNgao(GenericAPIView):
    def get(self, request):
        return render(request, '../templates/linh_ngao.html')
