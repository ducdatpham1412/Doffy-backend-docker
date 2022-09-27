from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
import pymongo
from utilities.renderers import PagingRenderer
from bson.objectid import ObjectId


class GetListGroupBuying(GenericAPIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PagingRenderer]

    def get_creator_name_avatar(self, user_id):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
            }
        except models.Profile.DoesNotExist:
            raise CustomError()

    def get(self, request, user_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        info_creator = self.get_creator_name_avatar(user_id)

        status_scope = [enums.status_active]
        if my_id == user_id:
            status_scope.append(enums.status_draft)

        sort_condition = [('status', pymongo.DESCENDING), ('created', pymongo.DESCENDING)
                          ] if my_id == user_id else [('created', pymongo.DESCENDING)]

        list_posts = mongoDb.discovery_post.find({
            'creator': user_id,
            'post_type': enums.post_group_buying,
            'status': {
                '$in': status_scope
            }
        }).sort(sort_condition).limit(take).skip((page_index-1)*take)
        total_posts = mongoDb.discovery_post.count({
            'creator': user_id,
            'post_type': enums.post_group_buying,
            'status': {
                '$in': status_scope
            }
        })

        list_post_group_buying = []
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

            status_joined = None
            if user_id != my_id:
                status_joined = enums.status_not_joined
                check_joined = mongoDb.join_group_buying.find_one({
                    'post_id': str(post['_id']),
                    'creator': my_id,
                    'status': {
                        '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
                    },
                })
                if check_joined:
                    status_joined = check_joined['status']

            temp = {
                'id': str(post['_id']),
                'postType': enums.post_group_buying,
                'topic': post['topic'],
                'content': post['content'],
                'images': link_images,
                'prices': post['prices'],
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalJoins': post['total_joins'],
                'deadlineDate': str(post['deadline_date']),
                'startDate': str(post['start_date']),
                'endDate': str(post['end_date']),
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'creatorLocation': info_creator['location'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'isDraft': post['status'] == enums.status_draft,
                'status': status_joined,
                'relationship': relationship,
            }
            list_post_group_buying.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': list_post_group_buying,
        }

        return Response(res, status=status.HTTP_200_OK)


class GetListPeopleJoined(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_info_user(self, user_id):
        profile = models.Profile.objects.get(user=user_id)
        return {
            'name': profile.name,
            'avatar': services.create_link_image(profile.avatar) if profile.avatar else ''
        }

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'status': enums.status_active,
        })
        if not post:
            raise CustomError()

        is_my_gb = post['creator'] == my_id

        list_joined = mongoDb.join_group_buying.find({
            'post_id': post_id,
            'status': {
                '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
            }
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
        total_users_joined = mongoDb.join_group_buying.count({
            'post_id': post_id,
            'status': {
                '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
            }
        })

        res_list_users = []
        for joined in list_joined:
            info_user = self.get_info_user(user_id=joined['creator'])
            temp = {
                'id': str(joined['_id']),
                'creator': joined['creator'],
                'creatorName': info_user['name'],
                'creatorAvatar': info_user['avatar'],
                'created': str(joined['created']),
                'status': None,
                'relationship': None,
            }
            if joined['creator'] == my_id:
                temp['relationship'] = enums.relationship_self
            elif is_my_gb:
                temp['status'] = joined['status']
            else:
                try:
                    models.Follow.objects.get(
                        follower=my_id, followed=joined['creator'])
                    temp['relationship'] = enums.relationship_following
                except models.Follow.DoesNotExist:
                    temp['relationship'] = enums.relationship_not_following
            res_list_users.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_users_joined,
            'data': res_list_users
        }

        return Response(res, status=status.HTTP_200_OK)
