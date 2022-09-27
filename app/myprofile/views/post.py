import json
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from myprofile.models import Profile
import requests


class CreatePost(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_user_name_avatar(self, user_id):
        profile = models.Profile.objects.get(user=user_id)
        return {
            'name': profile.name,
            'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
            'description': profile.description
        }

    def post(self, request):
        my_id = services.get_user_id_from_request(request)
        request_data = request.data
        now = services.get_datetime_now()

        is_draft = services.get_object(request_data, 'isDraft')
        if is_draft == None:
            raise CustomError()

        user_id = services.get_object(request_data, 'userId')
        if user_id == my_id:
            raise CustomError()
        temp_user_id = {}
        # consider to check is user_id is provider account
        if user_id:
            temp_user_id = {
                'user_id': user_id
            }

        status_post = enums.status_draft if is_draft else enums.status_active
        insert_post = {
            'post_type': enums.post_review,
            **temp_user_id,
            'content': request_data['content'],
            'images': request_data['images'],
            'stars': request_data['stars'],
            'topic': services.get_object(request_data, 'topic'),
            'feeling': services.get_object(request_data, 'feeling'),
            'location': services.get_object(request_data, 'location'),
            'link': services.get_object(request_data, 'link'),
            'total_reacts': 0,
            'total_comments': 0,
            'total_saved': 0,
            'creator': my_id,
            'created': now,
            'modified': now,
            'status': status_post,
        }
        mongoDb.discovery_post.insert_one(insert_post)

        res_images = []
        for img in insert_post['images']:
            res_images.append(services.create_link_image(img))

        info = self.get_user_name_avatar(my_id)

        temp_user_reviewed = {}
        if user_id:
            info_reviewed = self.get_user_name_avatar(user_id)
            temp_user_reviewed = {
                'userReviewed': {
                    'id': user_id,
                    'name': info_reviewed['name'],
                    'avatar': info_reviewed['avatar'],
                    'description': info_reviewed['description']
                }
            }

        res = {
            'id': str(insert_post['_id']),
            'postType': enums.post_review,
            'topic': insert_post['topic'],
            'feeling': insert_post['feeling'],
            'location': insert_post['location'],
            'content': insert_post['content'],
            'images': res_images,
            'stars': insert_post['stars'],
            'link': insert_post['link'],
            **temp_user_reviewed,
            'totalLikes': 0,
            'totalComments': 0,
            'totalSaves': 0,
            'creator': my_id,
            'creatorName': info['name'],
            'creatorAvatar': info['avatar'],
            'created': str(insert_post['created']),
            'isLiked': False,
            'isSaved': False,
            'isDraft': is_draft,
            'relationship': enums.relationship_self
        }

        return Response(res, status=status.HTTP_200_OK)


class EditPost(GenericAPIView):
    permission_classed = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        request_data = request.data

        update_post = {}

        content = services.get_object(request_data, 'content')
        stars = services.get_object(request_data, 'stars')
        topic = services.get_object(request_data, 'topic')
        feeling = services.get_object(request_data, 'feeling')
        location = services.get_object(request_data, 'location')
        link = services.get_object(request_data, 'link')
        is_draft = services.get_object(request_data, 'isDraft')

        if content != None:
            update_post['content'] = content
        if stars != None:
            update_post['stars'] = stars
        if feeling != None:
            update_post['feeling'] = feeling
        if topic != None:
            update_post['topic'] = topic
        if location != None:
            update_post['location'] = location
        if link != None:
            update_post['link'] = link
        if is_draft == False:
            update_post['status'] = enums.status_active
            update_post['created'] = services.get_datetime_now()
        update_post['modified'] = services.get_datetime_now()

        status_scope = [enums.status_draft]
        if is_draft != False:
            status_scope.append(enums.status_active)

        post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'creator': my_id,
                'status': {
                    '$in': status_scope,
                }
            },
            {
                '$set': update_post
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
                'status': enums.status_active
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
                'status': enums.status_active
            },
            {
                '$inc': {
                    'total_reacts': 1
                }
            }
        )
        if not check_post:
            raise CustomError()

        check_reputation = mongoDb.total_items.find_one_and_update(
            {
                'type': enums.total_reputation,
                'user_id': check_post['creator']
            },
            {
                '$inc': {
                    'value': 1,
                }
            }
        )
        if not check_reputation:
            mongoDb.total_items.insert_one({
                'type': enums.total_reputation,
                'user_id': check_post['creator'],
                'value': 1,
            })

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

        type_notification = None
        if post['post_type'] == enums.post_review:
            type_notification = enums.notification_like_post
        elif post['post_type'] == enums.post_group_buying:
            type_notification = enums.notification_like_gb

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
                'type': type_notification,
                'bubbleId': post_id,
            }
        })

        # Send notification
        insert_notification = {
            'type': type_notification,
            'user_id': post['creator'],
            'post_id': post_id,
            'creator': my_id,
            'created': services.get_datetime_now(),
            'status': enums.status_notification_not_read,
        }
        mongoDb.notification.insert_one(insert_notification)

        data_socket = {
            'id': str(insert_notification['_id']),
            'type': insert_notification['type'],
            'image': self.get_images(post['images']),
            'postId': post_id,
            'creator': my_id,
            'creatorName': profile.name,
            'creatorAvatar': services.create_link_image(profile.avatar),
            'created': str(insert_notification['created']),
            'status': insert_notification['status']
        }

        requests.post('http://chat:1412/notification/like-post',
                      data=json.dumps({
                          'receiver': post['creator'],
                          'data': data_socket,
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
                'status': enums.status_active
            },
            {
                '$inc': {
                    'total_reacts': -1
                }
            }
        )
        if not check_post:
            raise CustomError()

        check_reputation = mongoDb.total_items.find_one_and_update(
            {
                'type': enums.total_reputation,
                'user_id': check_post['creator']
            },
            {
                '$inc': {
                    'value': -1
                }
            }
        )
        if not check_reputation:
            raise CustomError()

        return Response(None, status=status.HTTP_200_OK)


class SavePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_and_save(self, post_id, user_id):
        check_saved = mongoDb.save.find_one({
            'type': enums.react_post,
            'saved_id': post_id,
            'creator': user_id,
            'status': enums.status_active
        })
        if check_saved:
            raise CustomError(error_message.had_saved_this_post,
                              error_key.had_saved_this_post)

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'status': enums.status_active
            },
            {
                '$inc': {
                    'total_saved': 1
                }
            }
        )
        if not check_post:
            raise CustomError()

        mongoDb.save.insert_one({
            'type': enums.save_post,
            'saved_id': post_id,
            'creator': user_id,
            'created': services.get_datetime_now(),
            'status': enums.status_active,
        })

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        self.check_and_save(post_id=post_id, user_id=my_id)
        # Send and Save notification will do later
        return Response(None, status=status.HTTP_200_OK)


class UnSavePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_and_un_save(self, post_id, user_id):
        check_saved = mongoDb.save.find_one_and_update(
            {
                'type': enums.save_post,
                'saved_id': post_id,
                'creator': user_id,
                'status': enums.status_active,
            },
            {
                '$set': {
                    'status': enums.status_not_active
                }
            }
        )
        if not check_saved:
            raise CustomError()

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'status': enums.status_active
            },
            {
                '$inc': {
                    'total_saved': -1
                }
            }
        )
        if not check_post:
            raise CustomError()

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        self.check_and_un_save(post_id=post_id, user_id=my_id)
        return Response(None, status=status.HTTP_200_OK)


class ArchivePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_review,
                'creator': my_id,
                'status': enums.status_active,
            },
            {
                '$set': {
                    'status': enums.status_archive,
                }
            }
        )

        if not check_post:
            raise CustomError()

        return Response(None, status=status.HTTP_200_OK)


class UnArchivePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        check_post = mongoDb.discovery_post.find_one_and_update(
            {
                '_id': ObjectId(post_id),
                'post_type': enums.post_review,
                'creator': my_id,
                'status': enums.status_archive,
            },
            {
                '$set': {
                    'status': enums.status_active,
                }
            }
        )

        if not check_post:
            raise CustomError()

        return Response(None, status=status.HTTP_200_OK)
