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
from authentication.models import User_Request


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

        status_scope = [enums.status_active,
                        enums.status_requesting_delete, enums.status_temporarily_closed]
        if my_id == user_id:
            status_scope.append(enums.status_draft)

        list_posts = mongoDb.discovery_post.aggregate([
            {
                '$match': {
                    'creator': user_id,
                    'post_type': enums.post_group_buying,
                    'status': {
                        '$in': status_scope,
                    }
                }
            },
            {
                '$sort': {
                    'created': pymongo.DESCENDING,
                    'status': pymongo.DESCENDING,
                }
            },
            {
                '$limit': take
            },
            {
                '$skip': (page_index - 1) * take,
            }
        ])
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

            relationship = enums.relationship_not_know
            request_update_price = None
            if post['creator'] == my_id:
                relationship = enums.relationship_self
                try:
                    user_request = User_Request.objects.get(type=enums.request_update_price, post_id=str(
                        post['_id']), creator=my_id, status=enums.status_active)
                    request_update_price = services.str_to_dict(
                        user_request.data)
                except User_Request.DoesNotExist:
                    pass

            status_joined = None
            deposit = None
            amount = None
            note = None
            if user_id != my_id:
                status_joined = enums.status_not_joined
                check_joined = mongoDb.join_personal.find_one({
                    'post_id': str(post['_id']),
                    'creator': my_id,
                    'status': enums.status_joined_not_bought
                })
                if check_joined:
                    status_joined = enums.status_joined_not_bought
                    deposit = check_joined['money']
                    amount = check_joined['amount']
                    note = check_joined['note']

            temp = {
                'id': str(post['_id']),
                'postType': enums.post_group_buying,
                'topic': post['topic'],
                'content': post['content'],
                'images': link_images,
                'retailPrice': post['retail_price'],
                'prices': post['prices'],
                'deposit': deposit,
                'amount': amount,
                'note': note,
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalGroups': post['total_groups'],
                'totalPersonals': post['total_personals'],
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'creatorLocation': info_creator['location'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'isDraft': post['status'] == enums.status_draft,
                'status': status_joined,
                'postStatus': post['status'],
                'relationship': relationship,
                'requestUpdatePrice': request_update_price,
            }
            list_post_group_buying.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': list_post_group_buying,
        }

        return Response(res, status=status.HTTP_200_OK)


class GetListGroupPeopleJoined(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_info_user(self, user_id):
        profile = models.Profile.objects.get(user=user_id)
        return {
            'name': profile.name,
            'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
            'phone': profile.user.phone,
        }

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'status': {
                '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
            }
        })
        if not post:
            raise CustomError()

        is_my_gb = post['creator'] == my_id

        list_group_people = mongoDb.join_group.aggregate([
            {
                '$match': {
                    'post_id': post_id,
                }
            },
            {
                '$sort': {
                    'created': pymongo.DESCENDING,
                }
            },
            {
                '$limit': take,
            },
            {
                '$skip': (page_index - 1) * take,
            }
        ])
        total_groups_join = mongoDb.join_group.count({
            'post_id': post_id
        })

        res_list_groups = []
        for group in list_group_people:
            list_joins = mongoDb.join_personal.aggregate([
                {
                    '$match': {
                        'join_group_id': str(group['_id']),
                        'status': {
                            '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
                        }
                    }
                },
                {
                    '$sort': {
                        'created': pymongo.DESCENDING,
                    }
                }
            ])
            res_list_joins = []
            for join in list_joins:
                info_user = self.get_info_user(user_id=join['creator'])
                relationship = None
                if not is_my_gb:
                    try:
                        models.Follow.objects.get(
                            follower=my_id, followed=join['creator'])
                        relationship = enums.relationship_following
                    except models.Follow.DoesNotExist:
                        relationship = enums.relationship_not_following
                res_list_joins.append({
                    'id': str(join['_id']),
                    'deposit': join['money'] if is_my_gb else None,
                    'amount': join['amount'] if is_my_gb else None,
                    'timeWillBuy': str(join['time_will_buy']) if is_my_gb else None,
                    'note': join['note'] if is_my_gb else None,
                    'creator': join['creator'],
                    'creatorName': info_user['name'],
                    'creatorAvatar': info_user['avatar'],
                    'creatorPhone': info_user['phone'] if is_my_gb else '',
                    'created': str(join['created']),
                    'status': join['status'] if is_my_gb else None,
                    'relationship': relationship,
                })
            res_list_groups.append({
                'id': str(group['_id']),
                'totalMembers': group['total_members'],
                'listPeople': res_list_joins,
                'created': str(group['created']),
            })

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_groups_join,
            'data': res_list_groups,
        }

        return Response(res, status=status.HTTP_200_OK)


# Only for supplier and their group booking
class GetListPeopleRetail(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def get_info_user(self, user_id):
        profile = models.Profile.objects.get(user=user_id)
        return {
            'name': profile.name,
            'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
            'phone': profile.user.phone,
        }

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'creator': my_id,
            'status': {
                '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
            }
        })
        if not post:
            raise CustomError()

        list_joined = mongoDb.join_personal.find({
            'post_id': post_id,
            'join_group_id': None,
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
        total_users_joined = mongoDb.join_personal.count({
            'post_id': post_id,
        })

        res_list_users = []
        for joined in list_joined:
            info_user = self.get_info_user(user_id=joined['creator'])
            temp = {
                'id': str(joined['_id']),
                'deposit': joined['money'],
                'amount': joined['amount'],
                'timeWillBuy': str(joined['time_will_buy']),
                'note': joined['note'],
                'creator': joined['creator'],
                'creatorName': info_user['name'],
                'creatorAvatar': info_user['avatar'],
                'creatorPhone': info_user['phone'],
                'created': str(joined['created']),
                'status': joined['status'],
                'relationship': enums.relationship_not_know,
            }
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
