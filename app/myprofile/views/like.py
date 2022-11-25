import json
from bson.objectid import ObjectId
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from myprofile.models import Profile
import requests


class LikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_and_like_post(self, post_id, user_id):
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
                'status': {
                    '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
                }
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

    def check_and_like_comment(self, comment_id, user_id):
        check_liked = mongoDb.reaction.find_one({
            'type': enums.react_comment,
            'reacted_id': comment_id,
            'creator': user_id,
            'status': enums.status_active,
        })
        if check_liked:
            raise CustomError()

        comment = mongoDb.discovery_comment.find_one_and_update(
            {
                '_id': ObjectId(comment_id),
                'status': enums.status_active,
            },
            {
                '$inc': {
                    'total_reacts': 1,
                }
            })
        if not comment:
            raise CustomError()

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(comment['post_id']),
            'status': {
                '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
            }
        })
        if not post:
            raise CustomError()

        mongoDb.reaction.insert_one({
            'type': enums.react_comment,
            'reacted_id': comment_id,
            'creator': user_id,
            'created': services.get_datetime_now(),
            'status': enums.status_active,
        })

        return comment, post

    def put(self, request, reacted_id):
        my_id = services.get_user_id_from_request(request)
        type_react = services.get_object(
            request.data, 'type', default=enums.react_post)

        type_notification = None
        profile = Profile.objects.get(user=my_id)
        creator_name = profile.name

        target_user_id = None
        image_notification = ''

        if type_react == enums.react_post:
            post = self.check_and_like_post(post_id=reacted_id, user_id=my_id)
            if post['post_type'] == enums.post_review:
                type_notification = enums.notification_like_post
            elif post['post_type'] == enums.post_group_buying:
                type_notification = enums.notification_like_gb
            target_user_id = post['creator']
            image_index_0 = services.get_index(post['images'], 0)
            if image_index_0:
                image_notification = services.create_link_image(image_index_0)

            services.send_notification({
                'contents': {
                    'vi': '{} thích bài đăng của bạn'.format(creator_name),
                    'en': '{} like your post'.format(creator_name)
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
                    'bubbleId': reacted_id,
                }
            })
        elif type_react == enums.react_comment:
            comment, post = self.check_and_like_comment(
                comment_id=reacted_id, user_id=my_id)
            type_notification = enums.notification_like_comment
            target_user_id = comment['creator']
            image_index_0 = services.get_index(post['images'], 0)
            if image_index_0:
                image_notification = services.create_link_image(image_index_0)

            services.send_notification({
                'contents': {
                    'vi': '{} thích bình luận của bạn'.format(creator_name),
                    'en': '{} like your comment'.format(creator_name)
                },
                'filters': [
                    {
                        'field': 'tag',
                        'key': 'userId',
                        'relation': '=',
                        'value': comment['creator'],
                    }
                ],
                'data': {
                    'type': type_notification,
                    'commentId': reacted_id,
                }
            })

        # Insert and send socket
        insert_notification = {
            'type': type_notification,
            'user_id': post['creator'],
            'post_id': reacted_id,
            'creator': my_id,
            'created': services.get_datetime_now(),
            'status': enums.status_notification_not_read,
        }
        mongoDb.notification.insert_one(insert_notification)

        if target_user_id:
            data_socket = {
                'id': str(insert_notification['_id']),
                'type': type_notification,
                'image': image_notification,
                'postId': reacted_id,
                'creator': my_id,
                'creatorName': profile.name,
                'creatorAvatar': services.create_link_image(profile.avatar),
                'created': str(insert_notification['created']),
                'status': insert_notification['status']
            }

            requests.post('http://chat:1412/notification/like-post',
                          data=json.dumps({
                              'receiver': target_user_id,
                              'data': data_socket,
                          }))

        return Response(None, status=status.HTTP_200_OK)


class UnLikePost(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def unlike_post(self, post_id, user_id):
        check_liked = mongoDb.reaction.find_one_and_update(
            {
                'type': enums.react_post,
                'reacted_id': post_id,
                'creator': user_id,
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
                'status': {
                    '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
                }
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

    def unlike_comment(self, comment_id, user_id):
        check_liked = mongoDb.reaction.find_one_and_update(
            {
                'type': enums.react_comment,
                'reacted_id': comment_id,
                'creator': user_id,
                'status': enums.status_active,
            },
            {
                '$set': {
                    'status': enums.status_not_active,
                }
            }
        )
        if not check_liked:
            raise CustomError()

        mongoDb.discovery_comment.update_one(
            {
                '_id': ObjectId(comment_id)
            },
            {
                '$inc': {
                    'total_reacts': -1
                }
            }
        )

    def put(self, request, reacted_id):
        my_id = services.get_user_id_from_request(request)
        type_react = services.get_object(
            request.data, 'type', default=enums.react_post)

        if type_react == enums.react_post:
            self.unlike_post(post_id=reacted_id, user_id=my_id)
        elif type_react == enums.react_comment:
            self.unlike_comment(comment_id=reacted_id, user_id=my_id)

        return Response(None, status=status.HTTP_200_OK)
