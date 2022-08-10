from utilities.exception.exception_handler import CustomError
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services, enums
from myprofile.models import Profile
from bson.objectid import ObjectId
import requests
import json


class GetListComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def filter_list_user_id(self, list_comments: list):
        result = []
        for comment in list_comments:
            try:
                result.index(comment['creator'])
            except ValueError:
                result.append(comment['creator'])
        return result

    def check_liked_comment(self, comment_id, user_id):
        check_reaction = mongoDb.reaction.find_one({
            'type': enums.react_comment,
            'reacted_id': comment_id,
            'creator': user_id,
            'status': enums.status_active,
        })
        return bool(check_reaction)

    def get_number_liked_comment(self, comment_id):
        return mongoDb.reaction.count({
            'type': enums.react_comment,
            'reacted_id': comment_id,
            'status': enums.status_active,
        })

    def get_list_comments_reply(self, list_comments: list, str_comment_id):
        res = []
        for comment in list_comments:
            if comment['replied_id'] == str_comment_id:
                res.append(comment)
        return res

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        list_comments = mongoDb.discovery_comment.find({
            'post_id': post_id,
            'status': enums.status_active
        })
        list_comments = list(list_comments)

        id_name_avatar_object = {}
        for user_id_comment in self.filter_list_user_id(list_comments):
            profile = Profile.objects.get(user=user_id_comment)
            id_name_avatar_object['{}'.format(user_id_comment)] = {
                'id': user_id_comment,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar),
            }

        # Result
        res = []
        for comment in list_comments:
            if comment['replied_id'] == None:
                str_comment_id = str(comment['_id'])
                is_liked = self.check_liked_comment(
                    comment_id=str_comment_id, user_id=my_id)
                number_likes = self.get_number_liked_comment(
                    comment_id=str_comment_id)

                id_name_avatar = id_name_avatar_object['{}'.format(
                    comment['creator'])]

                # Comments reply
                list_replies = []
                for comment_reply in self.get_list_comments_reply(list_comments, str_comment_id):
                    id_name_avatar_reply = id_name_avatar_object['{}'.format(
                        comment_reply['creator'])]
                    is_liked_reply = self.check_liked_comment(
                        comment_id=str(comment_reply['_id']), user_id=my_id)
                    number_likes_reply = self.get_number_liked_comment(
                        comment_id=str(comment_reply['_id']))

                    list_replies.append({
                        'id': str(comment_reply['_id']),
                        'content': comment_reply['content'],
                        'images': comment_reply['images'],
                        'numberLikes': number_likes_reply,
                        'isLiked': is_liked_reply,
                        'creator': id_name_avatar_reply['id'],
                        'creatorName': id_name_avatar_reply['name'],
                        'creatorAvatar': id_name_avatar_reply['avatar'],
                        'created': str(comment_reply['created']),
                    })

                # Result
                res.append({
                    'id': str(comment['_id']),
                    'content': comment['content'],
                    'images': comment['images'],
                    'numberLikes': number_likes,
                    'isLiked': is_liked,
                    'creator': id_name_avatar['id'],
                    'creatorName': id_name_avatar['name'],
                    'creatorAvatar': id_name_avatar['avatar'],
                    'created': str(comment['created']),
                    'listCommentsReply': list_replies,
                })

        return Response(res, status=status.HTTP_200_OK)


class DeleteComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, comment_id):
        my_id = services.get_user_id_from_request(request)

        check_comment = mongoDb.discovery_comment.find_one_and_update(
            {
                '_id': ObjectId(comment_id),
                'creator': my_id
            },
            {
                '$set': {
                    'status': enums.status_not_active
                }
            }
        )
        if not check_comment:
            raise CustomError()

        requests.post('http://chat:1412/comment/delete-comment', data=json.dumps({
            'postId': check_comment['post_id'],
            'commentId': comment_id
        }))

        return Response(None, status=status.HTTP_200_OK)
