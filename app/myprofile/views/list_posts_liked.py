import json
from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
from myprofile.models import Profile
from utilities.renderers import PagingRenderer
import pymongo
from authentication.models import User_Request


class GetListPostLiked(GenericAPIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PagingRenderer]

    def get_creator_name_avatar(self, user_id):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar)
            }
        except models.Profile.DoesNotExist:
            raise CustomError()

    def get_profile(self, user_id: int):
        try:
            profile = models.Profile.objects.get(user=user_id)
            return {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
                'description': profile.description,
            }
        except models.Profile.DoesNotExist:
            return services.fake_user_profile

    def filter_list_user_id(self, list_posts: list):
        result = []
        for post in list_posts:
            try:
                result.index(post['creator'])
            except ValueError:
                result.append(post['creator'])
        return result

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])
        post_types = services.get_object(request.query_params, 'post_types')
        post_types = json.loads(post_types) if post_types else [
            enums.post_review, enums.post_group_buying]

        list_reactions = mongoDb.reaction.aggregate([
            {
                '$match': {
                    'type': enums.react_post,
                    'creator': my_id,
                    'status': enums.status_active,
                },
            },
            {
                '$lookup': {
                    'from': 'discovery_post',
                    'let': {
                        'post_id': {
                            '$toObjectId': '$reacted_id'
                        }
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$and': [
                                        {'$eq': ['$_id', '$$post_id']},
                                        {'$eq': ['$status',
                                                 enums.status_active]},
                                        {'$in': ['$post_type', post_types]}
                                    ]
                                }
                            }
                        }
                    ],
                    'as': 'post'
                }
            },
            {
                '$match': {
                    'post': {
                        '$ne': []
                    }
                }
            },
            {
                '$sort': {
                    'created': pymongo.DESCENDING,
                },
            },
            {
                '$limit': take,
            },
            {
                '$skip': (page_index - 1) * take
            },
        ])

        total_posts_liked = mongoDb.reaction.count({
            'type': enums.react_post,
            'creator': my_id,
            'status': enums.status_active
        })

        list_posts = []
        for reaction in list_reactions:
            list_posts.append(reaction['post'][0])

        id_name_avatar_object = {}
        for user_id in self.filter_list_user_id(list_posts):
            profile = Profile.objects.get(user=user_id)
            id_name_avatar_object['{}'.format(user_id)] = {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar),
                'location': profile.location,
            }

        res_posts_liked = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                link_images.append(services.create_link_image(image))

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            if post['post_type'] == enums.post_review:
                check_saved = mongoDb.save.find_one({
                    'type': enums.save_post,
                    'saved_id': str(post['_id']),
                    'creator': my_id,
                    'status': enums.status_active,
                })
                is_saved = bool(check_saved)

                user_reviewed = None
                user_id = services.get_object(post, 'user_id')
                if user_id:
                    profile = self.get_profile(user_id)
                    user_reviewed = {
                        'id': user_id,
                        'name': profile['name'],
                        'avatar': profile['avatar'],
                        'description': profile['description'],
                        'location': profile['location']
                    }

                temp = {
                    'id': str(post['_id']),
                    'postType': enums.post_review,
                    'topic': post['topic'],
                    'feeling': post['feeling'],
                    'location': post['location'],
                    'content': post['content'],
                    'images': link_images,
                    'stars': post['stars'],
                    'link': post['link'],
                    'userReviewed': user_reviewed,
                    'totalLikes': post['total_reacts'],
                    'totalComments': post['total_comments'],
                    'totalSaved': post['total_saved'],
                    'creator': post['creator'],
                    'creatorName': info_creator['name'],
                    'creatorAvatar': info_creator['avatar'],
                    'created': str(post['created']),
                    'isLiked': True,
                    'isSaved': is_saved,
                    'isArchived': False,
                    'relationship': relationship,
                }

                res_posts_liked.append(temp)

            elif post['post_type'] == enums.post_group_buying:
                status_joined = enums.status_not_joined
                deposit = None
                amount = None
                note = None
                request_update_price = None
                if post['creator'] == my_id:
                    try:
                        user_request = User_Request.objects.get(type=enums.request_update_price, post_id=str(
                            post['_id']), creator=my_id, status=enums.status_active)
                        request_update_price = services.str_to_dict(
                            user_request.data)
                    except User_Request.DoesNotExist:
                        pass

                check_joining = mongoDb.join_personal.find_one({
                    'post_id': str(post['_id']),
                    'creator': my_id,
                    'status': enums.status_joined_not_bought,
                })
                if check_joining:
                    status_joined = check_joining['status']
                    deposit = check_joining['money']
                    amount = check_joining['amount']
                    note = check_joining['note']

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
                    'isLiked': True,
                    'status': status_joined,
                    'postStatus': post['status'],
                    'relationship': relationship,
                    'requestUpdatePrice': request_update_price,
                }
                res_posts_liked.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts_liked,
            'data': res_posts_liked
        }

        return Response(res, status=status.HTTP_200_OK)
