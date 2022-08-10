import json
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from myprofile import models
from myprofile import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
import pymongo
from myprofile.models import Profile
import requests


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
        request_data = request.data
        now = services.get_datetime_now()

        insert_post = {
            'topic': services.get_object(request_data, 'topic'),
            'feeling': services.get_object(request_data, 'feeling'),
            'location': services.get_object(request_data, 'location'),
            'content': request_data['content'],
            'images': request_data['images'],
            'stars': request_data['stars'],
            'link': services.get_object(request_data, 'link'),
            'total_reacts': 0,
            'total_comments': 0,
            'creator': my_id,
            'created': now,
            'modified': now,
            'status': enums.status_active,
        }
        mongoDb.discovery_post.insert_one(insert_post)

        res_images = []
        for img in insert_post['images']:
            res_images.append(services.create_link_image(img))

        info = self.get_user_name_avatar(my_id)

        res = {
            'id': str(insert_post['_id']),
            'topic': insert_post['topic'],
            'feeling': insert_post['feeling'],
            'location': insert_post['location'],
            'content': insert_post['content'],
            'images': res_images,
            'stars': insert_post['stars'],
            'totalLikes': 0,
            'totalComments': 0,
            'creator': my_id,
            'creatorName': info['name'],
            'creatorAvatar': info['avatar'],
            'created': str(insert_post['createdTime']),
            'relationship': enums.relationship_self
        }

        return Response(res, status=status.HTTP_200_OK)


class EditPost(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'creator': my_id,
            },
            {
                '$set': request.data
            }
        )

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


class DeletePost(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'creator': my_id,
            },
            {
                '$set': {
                    'status': enums.status_not_active,
                }
            }
        )

        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        return Response(None, status=status.HTTP_200_OK)


class GetListPost(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_creator_name_avatar(self, user_id):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar)
            }
        except models.Profile.DoesNotExist:
            raise CustomError()

    def get(self, request, user_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        info_creator = self.get_creator_name_avatar(user_id)

        list_posts = mongoDb.discovery_post.find({
            'creator': user_id,
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)

        res = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                link_images.append(services.create_link_image(image))

            check_liked = mongoDb.reaction.find_one({
                'type': enums.react_post,
                'reacted_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active
            })
            is_liked = bool(check_liked)

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            temp = {
                'id': str(post['_id']),
                'topic': post['topic'],
                'feeling': post['feeling'],
                'location': post['location'],
                'content': post['content'],
                'images': link_images,
                'stars': post['stars'],
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'relationship': relationship
            }

            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)


class LikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_and_like(self, post_id, user_id):
        check_liked = mongoDb.reaction.find_one({
            'type': enums.react_post,
            'reacted_id': post_id,
            'creator': user_id,
            'status': enums.status_active,
        })
        if check_liked:
            raise CustomError(error_message.you_have_liked_this_post,
                              error_key.you_have_liked_this_post)

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
            },
            {
                '$inc': {
                    'total_reacts': 1
                }
            }
        )
        if not check_post:
            raise CustomError()

        mongoDb.reaction.insert_one({
            'type': enums.react_post,
            'reacted_id': post_id,
            'creator': user_id,
            'created': services.get_datetime_now(),
            'status': enums.status_active,
        })

        return check_post

    def get_images(self, list_images: list):
        try:
            temp = services.create_link_image(list_images[0])
            return temp
        except IndexError:
            return ''

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        post = self.check_and_like(post_id=post_id, user_id=my_id)

        profile = Profile.objects.get(user=my_id)
        target_name = profile.name

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
                    'value': post['creator']
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
                'userId': post['creator']
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
                          'receiver': post['creator'],
                          'data': data_notification
                      }))

        return Response(None, status=status.HTTP_200_OK)


class UnLikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        check_liked = mongoDb.reaction.find_one_and_update(
            {
                'type': enums.react_post,
                'reacted_id': post_id,
                'creator': my_id,
                'status': enums.status_active
            },
            {
                '$set': {
                    'status': enums.status_not_active
                }
            }
        )
        if not check_liked:
            raise CustomError(error_message.you_not_liked_this_post,
                              error_key.you_not_liked_this_post)

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
            },
            {
                '$inc': {
                    'total_reacts': -1
                }
            }
        )
        if not check_post:
            raise CustomError()

        return Response(None, status=status.HTTP_200_OK)
