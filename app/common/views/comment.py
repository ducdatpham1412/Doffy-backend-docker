from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services, enums
from setting.models import Information
from bson.objectid import ObjectId
from myprofile.models import Profile
import requests
import json


class GetListComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    list_user_i_know = []
    my_id = 0

    def check_i_have_know(self, user_id):
        if self.my_id == user_id:
            return True
        for id in self.list_user_i_know:
            if id == user_id:
                return True
        return False

    def get_avatar_name(self, user_id: int, had_know: bool):
        profile = Profile.objects.get(user=user_id)

        if had_know:
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar)
            }

        information = Information.objects.get(user=user_id)
        return {
            'name': profile.anonymous_name,
            'avatar': services.choose_private_avatar(information.gender)
        }

    def get(self, request, bubble_id):
        self.my_id = services.get_user_id_from_request(request)
        self.list_user_i_know = services.get_list_user_id_i_know(self.my_id)

        post = mongoDb.profilePost.find_one({
            '_id': ObjectId(bubble_id)
        })

        id_name_avatar_object = {}

        for user_comment in post['listUsersComment']:
            check_i_had_know = self.check_i_have_know(user_comment)

            if user_comment == self.my_id:
                avatar_name = self.get_avatar_name(self.my_id, True)
            else:
                avatar_name = self.get_avatar_name(
                    user_comment, check_i_had_know)

            id_name_avatar_object['{}'.format(user_comment)] = {
                'id': user_comment if check_i_had_know else None,
                'name': avatar_name['name'],
                'avatar': avatar_name['avatar'],
            }

        res = []
        for comment in post['listComments']:
            is_liked = services.check_include(
                list=comment['peopleLike'], value=self.my_id)
            id_name_avatar = id_name_avatar_object['{}'.format(
                comment['creatorId'])]

            list_replies = []
            for comment_reply in comment['listCommentsReply']:
                id_name_avatar_reply = id_name_avatar_object['{}'.format(
                    comment_reply['creatorId'])]
                is_liked_reply = services.check_include(
                    list=comment_reply['peopleLike'], value=self.my_id)

                list_replies.append({
                    'id': comment_reply['id'],
                    'content': comment_reply['content'],
                    'numberLikes': len(comment_reply['peopleLike']),
                    'isLiked': is_liked_reply,
                    'creatorId': id_name_avatar_reply['id'],
                    'creatorName': id_name_avatar_reply['name'],
                    'creatorAvatar': id_name_avatar_reply['avatar'],
                    'createdTime': services.get_local_string_date_time(comment_reply['createdTime']),
                })

            res.append({
                'id': comment['id'],
                'content': comment['content'],
                'numberLikes': len(comment['peopleLike']),
                'isLiked': is_liked,
                'creatorId': id_name_avatar['id'],
                'creatorName': id_name_avatar['name'],
                'creatorAvatar': id_name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(comment['createdTime']),
                'listCommentsReply': list_replies,
            })

        return Response(res, status=status.HTTP_200_OK)


class AddComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def comment_replied(self, data):
        try:
            return data['commentReplied']
        except KeyError:
            return ''

    def get_name_avatar(self, your_id):
        profile = Profile.objects.get(user=your_id)
        information = Information.objects.get(user=your_id)

        return {
            'name': profile.anonymous_name,
            'avatar': services.choose_private_avatar(information.gender)
        }

    def post(self, request, bubble_id):
        my_id = services.get_user_id_from_request(request)

        new_comment = {
            'id': str(ObjectId()),
            'content': request.data['content'],
            'creatorId': my_id,
            'createdTime': str(services.get_datetime_now()),
            'peopleLike': []
        }

        comment_replied_id = self.comment_replied(request.data)
        name_avatar = self.get_name_avatar(my_id)

        if comment_replied_id:
            profile_post = mongoDb.profilePost.find_one_and_update(
                {
                    '_id': ObjectId(bubble_id),
                    'listComments.id': comment_replied_id,
                },
                {
                    '$addToSet': {
                        'listUsersComment': my_id
                    },
                    '$push': {
                        'listComments.$.listCommentsReply': new_comment
                    },
                    '$inc': {
                        'totalComments': 1,
                    }
                }
            )
            new_comment = {
                'id': new_comment['id'],
                'content': new_comment['content'],
                'numberLikes': 0,
                'isLiked': False,
                'creatorId': new_comment['creatorId'],
                'creatorName': name_avatar['name'],
                'creatorAvatar': name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(new_comment['createdTime']),
                'replyOf': comment_replied_id,
            }

        else:
            new_comment = {
                **new_comment,
                'listCommentsReply': []
            }
            profile_post = mongoDb.profilePost.find_one_and_update(
                {
                    '_id': ObjectId(bubble_id)
                },
                {
                    '$addToSet': {
                        'listUsersComment': my_id
                    },
                    '$push': {
                        'listComments': new_comment
                    },
                    '$inc': {
                        'totalComments': 1
                    }
                }
            )

            new_comment = {
                'id': new_comment['id'],
                'content': new_comment['content'],
                'numberLikes': 0,
                'isLiked': False,
                'creatorId': new_comment['creatorId'],
                'creatorName': name_avatar['name'],
                'creatorAvatar': name_avatar['avatar'],
                'createdTime': services.get_local_string_date_time(new_comment['createdTime']),
                'listCommentsReply': new_comment['listCommentsReply'],
            }

        # Notification
        image_notification = name_avatar['avatar']
        try:
            temp = services.create_link_image(
                profile_post['images'][0])
            image_notification = temp
        except IndexError:
            pass
        content_notification = '{} đã bình luận về bài đăng của bạn'.format(
            name_avatar['name'])

        data_notification = {
            'id': new_comment['id'],
            'type': enums.notification_comment,
            'content': content_notification,
            'image': image_notification,
            'creatorId': my_id,
            'bubbleId': bubble_id,
            'hadRead': False,
        }
        mongoDb.notification.find_one_and_update(
            {
                'userId': profile_post['creatorId']
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

        # send onesignal
        services.send_notification({
            'contents': {
                'vi': content_notification,
                'en': '{} commented on your post'.format(name_avatar['name'])
            },
            'filters': [
                {
                    'field': 'tag',
                    'key': 'userId',
                    'relation': '=',
                    'value': profile_post['creatorId']
                }
            ],
            'data': {
                'type': enums.notification_comment,
                'bubbleId': bubble_id,
            }
        })

        # socket notification
        requests.post('http://chat:1412/notification/comment', data=json.dumps({
            'receiver': profile_post['creatorId'],
            'data': data_notification,
        }))

        return Response(new_comment, status=status.HTTP_200_OK)
