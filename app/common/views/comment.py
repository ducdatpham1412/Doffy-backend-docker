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
from pymongo import ASCENDING
from utilities.renderers import PagingRenderer


class GetListComment(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

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

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        page_index = int(request.query_params['pageIndex'])
        take = int(request.query_params['take'])
        replied_id = services.get_object(request.query_params, 'replied_id')
        replied_id = str(replied_id) if replied_id else None

        condition = {
            'post_id': post_id,
            'replied_id': replied_id,
            'status': enums.status_active,
        }

        list_comments = mongoDb.discovery_comment.aggregate([
            {
                '$match': condition,
            },
            {
                '$sort': {
                    'created': ASCENDING
                }
            },
            {
                '$limit': take,
            },
            {
                '$skip': (page_index - 1) * take,
            }
        ])
        list_comments = list(list_comments)

        total_comments = mongoDb.discovery_comment.count(condition)

        id_name_avatar_object = {}
        for user_id_comment in self.filter_list_user_id(list_comments):
            profile = Profile.objects.get(user=user_id_comment)
            id_name_avatar_object['{}'.format(user_id_comment)] = {
                'id': user_id_comment,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar),
            }

        # Result
        res_comments = []
        for comment in list_comments:
            str_comment_id = str(comment['_id'])
            is_liked = self.check_liked_comment(
                comment_id=str_comment_id, user_id=my_id)
            id_name_avatar = id_name_avatar_object['{}'.format(
                comment['creator'])]

            res_comments.append({
                'id': str(comment['_id']),
                'content': comment['content'],
                'images': comment['images'],
                'totalLikes': comment['total_reacts'],
                'totalReplies': comment['total_replies'],
                'isLiked': is_liked,
                'creator': id_name_avatar['id'],
                'creatorName': id_name_avatar['name'],
                'creatorAvatar': id_name_avatar['avatar'],
                'created': str(comment['created']),
            })

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_comments,
            'data': res_comments,
        }

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
