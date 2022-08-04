import json
from common.serializers import GetPassportSerializer
from authentication.models import User
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from myprofile import models
from myprofile.api import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from setting.models import Block, Information
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
import pymongo
from utilities.disableObject import DisableObject
from myprofile.models import Profile
import requests
from authentication.query.user_request import CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT
from findme.mysql import mysql_select


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
            Block.objects.get(block=your_id, blocked=my_id)
            return True
        except Block.DoesNotExist:
            try:
                Block.objects.get(block=my_id, blocked=your_id)
                return True
            except Block.DoesNotExist:
                return False

    def check_is_locking_account(self, your_id):
        user_requests = mysql_select(
            CHECK_USER_IS_REQUEST_OR_LOCK_ACCOUNT(user_id=your_id))

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
            'name': data_profile['name'],
            'avatar': data_profile['avatar'],
            'cover': data_profile['cover'],
            'description': data_profile['description'],
            'followers': data_profile['followers'],
            'followings': data_profile['followings'],
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
        id = services.get_user_id_from_request(request)
        newProfile = request.data

        myProfile = self.get_object(id)

        serializer = serializers.EditProfileSerializer(
            myProfile, data=newProfile)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(None, status=status.HTTP_200_OK)


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


class CreatePost(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_user_name_avatar(self, user_id):
        query = models.Profile.objects.get(user=user_id)
        data_profile = serializers.ProfileSerializer(query).data
        return {
            'name': data_profile['name'],
            'avatar': data_profile['avatar']
        }

    def post(self, request):
        my_id = services.get_user_id_from_request(request)

        insert_post = {
            'content': request.data['content'],
            'images': request.data['images'],
            'totalLikes': 0,
            'totalComments': 0,
            'peopleLike': [],
            'listComments': [],
            'listUsersComment': [],
            'creatorId': my_id,
            'createdTime': services.get_datetime_now(),
            'priority': 1,
            'color': request.data['color'],
            'name': request.data['name']
        }
        mongoDb.profilePost.insert_one(insert_post)

        mongoDb.analysis.find_one_and_update(
            {
                'type': 'priority'
            },
            {
                '$inc': {
                    'totalPosts': 1,
                    'oneLength': 1
                },
                '$push': {
                    'one': str(insert_post['_id'])
                }
            }
        )

        res_images = []
        for img in insert_post['images']:
            res_images.append(services.create_link_image(img))

        info = self.get_user_name_avatar(my_id)

        res = {
            'id': str(insert_post['_id']),
            'content': insert_post['content'],
            'images': res_images,
            'totalLikes': 0,
            'totalComments': 0,
            'creatorId': my_id,
            'creatorName': info['name'],
            'creatorAvatar': info['avatar'],
            'createdTime': str(insert_post['createdTime']),
            'color': insert_post['color'],
            'name': insert_post['name'],
            'isLiked': False,
            'relationship': enums.relationship_self
        }

        return Response(res, status=status.HTTP_200_OK)


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


class EditPost(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        id = services.get_user_id_from_request(request)

        post = mongoDb.profilePost.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'creatorId': id,
            },
            {
                '$set': request.data
            }
        )

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


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


class DeletePost(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        id = services.get_user_id_from_request(request)

        post = mongoDb.profilePost.find_one_and_delete({
            '_id': ObjectId(post_id),
            'creatorId': id,
        })

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)
        DisableObject.add_disable_post_or_message(
            enums.disable_profile_post, post)

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


class GetListPost(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_creator_name_avatar(self, user_id):
        query = models.Profile.objects.get(user=user_id)
        data_profile = serializers.ProfileSerializer(query).data
        return {
            'name': data_profile['name'],
            'avatar': data_profile['avatar']
        }

    def get(self, request, user_id):
        id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_posts = mongoDb.profilePost.find({
            'creatorId': user_id,
        }).sort([('createdTime', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)

        res = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                link_images.append(
                    services.create_link_image(image) if image else '')
            relationship = enums.relationship_self if post[
                'creatorId'] == id else enums.relationship_not_know

            # people_like = []
            is_liked = False
            for people in post['peopleLike']:
                # people_like.append({
                #     'id': people['id'],
                #     'createdTime': str(people['createdTime'])
                # })
                if not is_liked and people['id'] == id:
                    is_liked = True
                    break

            info_creator = self.get_creator_name_avatar(user_id)

            temp = {
                'id': str(post['_id']),
                'content': post['content'],
                'images': link_images,
                'totalLikes': post['totalLikes'],
                'totalComments': post['totalComments'],
                'creatorId': post['creatorId'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'createdTime': str(post['createdTime']),
                'color': post['color'],
                'name': post['name'],
                'isLiked': is_liked,
                'relationship': relationship
            }

            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)


class LikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_object(self, post_id, user_id):
        check = mongoDb.profilePost.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'peopleLike.id': {
                    '$ne': user_id
                }
            },
            {
                '$push': {
                    'peopleLike': {
                        '$each': [{
                            'id': user_id,
                            'createdTime': services.get_datetime_now()
                        }],
                        '$position': 0
                    }
                },
                '$inc': {
                    'totalLikes': 1
                }
            }
        )

        if not check:
            raise CustomError(error_message.you_have_liked_this_post,
                              error_key.you_have_liked_this_post)
        return check

    def get_images(self, list_images: list):
        try:
            temp = services.create_link_image(list_images[0])
            return temp
        except IndexError:
            return ''

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        post = self.get_object(post_id, my_id)

        list_user_i_know = services.get_list_user_id_i_know(my_id)
        hadFollow = services.check_had_i_know(
            list_user_id=list_user_i_know, partner_id=post['creatorId'])

        profile = Profile.objects.get(user=my_id)

        target_name = profile.name if hadFollow else profile.anonymous_name

        # Push notification one signal
        services.send_notification({
            'contents': {
                'vi': '{} thích bài đăng của bạn'.format(target_name),
                'en': '{} like your post'.format(target_name)
            },
            'filters': [
                {
                    'field': 'tag',
                    'key': 'userId',
                    'relation': '=',
                    'value': post['creatorId']
                }
            ],
            'data': {
                'type': enums.notification_like_post,
                'bubbleId': post_id,
            }
        })

        # Send notification
        data_notification = {
            'id': str(ObjectId()),
            'type': enums.notification_like_post,
            'content': '{} thích bài đăng của bạn 😎'.format(target_name),
            'image': self.get_images(post['images']),
            'creatorId': my_id,
            'bubbleId': post_id,
            'hadRead': False,
        }

        mongoDb.notification.find_one_and_update(
            {
                'userId': post['creatorId']
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

        requests.post('http://chat:1412/notification/like-post',
                      data=json.dumps({
                          'receiver': post['creatorId'],
                          'data': data_notification
                      }))

        return Response(None, status=status.HTTP_200_OK)


class UnLikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_object(self, post_id, user_id):
        check = mongoDb.profilePost.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'peopleLike.id': user_id
            },
            {
                '$pull': {
                    'peopleLike': {
                        'id': user_id
                    }
                },
                '$inc': {
                    'totalLikes': -1
                }
            }
        )

        if not check:
            raise CustomError(error_message.you_not_liked_this_post,
                              error_key.you_not_liked_this_post)

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        self.get_object(post_id, my_id)
        return Response(None, status=status.HTTP_200_OK)


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
        list_user_i_know = services.get_list_user_id_i_know(self.my_id)

        res = []
        for id in list_id:
            profile = models.Profile.objects.get(user=id)
            had_i_know = True if self.my_id == id else services.check_had_i_know(
                list_user_id=list_user_i_know, partner_id=id)

            avatar = services.create_link_image(profile.avatar)
            if not had_i_know:
                information = Information.objects.get(user=id)
                avatar = services.choose_private_avatar(information.gender)

            temp = {
                'id': profile.user.id if had_i_know else None,
                'name': profile.name if had_i_know else profile.anonymous_name,
                'avatar': avatar,
                'description': profile.description if had_i_know else '',
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


class GetListNotification(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        page_index = int(request.query_params['pageIndex'])
        take = int(request.query_params['take'])

        start = int((page_index-1) * take)
        end = int(page_index * take)

        data_notification = mongoDb.notification.find_one({
            'userId': my_id
        })
        res = data_notification['list'][start:end]

        return Response(res, status=status.HTTP_200_OK)
