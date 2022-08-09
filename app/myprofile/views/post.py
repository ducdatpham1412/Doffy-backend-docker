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

        # Update status here

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
