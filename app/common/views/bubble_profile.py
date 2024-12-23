from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utilities import enums, services
from myprofile.models import Profile
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
import pymongo
from bson.objectid import ObjectId
import json
from utilities.renderers import PagingRenderer
from authentication.models import User_Request


class GetListBubbleProfile(GenericAPIView):
    permission_classes = [AllowAny, ]
    renderer_classes = [PagingRenderer, ]

    def filter_list_user_id(self, list_posts: list):
        result = []
        for post in list_posts:
            try:
                result.index(post['creator'])
            except ValueError:
                result.append(post['creator'])
        return result

    def get_profile(self, user_id: int):
        try:
            profile = Profile.objects.get(user=user_id)
            return {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
                'description': profile.description,
            }
        except Profile.DoesNotExist:
            return services.fake_user_profile

    def check_is_liked(self, user_id: int or None, post_id: str):
        if user_id == None:
            return True

        check_liked = mongoDb.reaction.find_one({
            'type': enums.react_post,
            'reacted_id': post_id,
            'creator': user_id,
            'status': enums.status_active
        })
        return bool(check_liked)

    def check_is_saved(self, user_id: int or None, post_id: str):
        if user_id == None:
            return True
        check_saved = mongoDb.save.find_one({
            'type': enums.save_post,
            'saved_id': post_id,
            'creator': user_id,
            'status': enums.status_active,
        })
        return bool(check_saved)

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_topics = services.get_object(request.query_params, 'topics')
        list_topics = json.loads(list_topics) if list_topics else []

        list_post_types = services.get_object(
            request.query_params, 'postTypes')
        list_post_types = json.loads(
            list_post_types) if list_post_types else []

        prices = services.get_object(request.query_params, 'prices')
        include_me = services.get_object(request.query_params, 'include_me')

        search = services.get_object(request.query_params, 'search')
        search = " ".join(str(search).split()) if search else None

        services.get_list_user_block(user_id=my_id)

        list_user_not_in = [my_id] if not include_me else []
        list_user_not_in.extend(services.get_list_user_block(my_id))

        condition = {
            'creator': {
                '$nin': list_user_not_in,
            },
            'status': enums.status_active
        }

        if len(list_topics) > 0:
            condition['topic'] = {
                '$in': list_topics
            }

        if len(list_post_types) > 0:
            condition['post_type'] = {
                '$in': list_post_types
            }

        if prices:
            prices = json.loads(prices)
            start_price = prices[0]
            end_price = prices[1]
            condition['$expr'] = {
                '$cond': {
                    'if': {
                        '$eq': ['$post_type', enums.post_group_buying]
                    },
                    'then': {
                        # All element in array valid -> $allElementTrue
                        '$anyElementTrue': {
                            '$map': {
                                'input': '$prices',
                                'as': 'price',
                                'in': {
                                    '$and': [
                                        {
                                            '$gte': [
                                                {'$toDouble': '$$price.value'}, start_price
                                            ]
                                        },
                                        {
                                            '$lte': [
                                                {'$toDouble': '$$price.value'}, end_price
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'else': {}
                }
            }

        if search:
            condition['$text'] = {
                '$search': "\"{}\"".format(search),
                '$caseSensitive': False,
            }

        total_posts = mongoDb.discovery_post.count(condition)
        if total_posts == 0:
            condition.pop('creator')
            condition['$text'] = {
                '$search': "{}".format(search),
                '$caseSensitive': False,
            }
        total_posts = mongoDb.discovery_post.count(condition)

        # If check have post, make query, else return result to avoid time query
        if total_posts > 0:
            list_posts = mongoDb.discovery_post.aggregate([
                {
                    '$match': condition
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
            list_posts = list(list_posts)

            id_name_avatar_object = {}
            for user_id in self.filter_list_user_id(list_posts):
                profile = self.get_profile(user_id)
                id_name_avatar_object['{}'.format(user_id)] = {
                    'id': user_id,
                    'name': profile['name'],
                    'avatar': profile['avatar'],
                    'location': profile['location'],
                }

            res_posts = []
            for post in list_posts:
                link_images = []
                for image in post['images']:
                    temp = services.create_link_image(image)
                    link_images.append(temp)

                is_liked = self.check_is_liked(
                    user_id=my_id, post_id=str(post['_id']))

                info_creator = id_name_avatar_object['{}'.format(
                    post['creator'])]

                # post review
                if post['post_type'] == enums.post_review:
                    is_saved = self.check_is_saved(
                        user_id=my_id, post_id=str(post['_id']))

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

                    res_posts.append({
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
                        'isLiked': is_liked,
                        'isSaved': is_saved,
                        'relationship': enums.relationship_not_know
                    })

                # post group buying
                elif post['post_type'] == enums.post_group_buying:
                    status_joined = enums.status_not_joined
                    deposit = None
                    amount = None
                    note = None
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

                    if user_id != None:
                        check_joined = mongoDb.join_personal.find_one({
                            'post_id': str(post['_id']),
                            'creator': user_id,
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
                        'status': status_joined,
                        'postStatus': post['status'],
                        'relationship': relationship,
                        'requestUpdatePrice': request_update_price,
                    }
                    res_posts.append(temp)

            res = {
                'take': take,
                'pageIndex': page_index,
                'totalItems': total_posts,
                'result': None,
                'data': res_posts,
            }

        # Return no data
        else:
            res = {
                'take': take,
                'pageIndex': page_index,
                'totalItems': 0,
                'result': None,
                'data': []
            }

        # Add result, remove post_type here
        if search:
            if services.get_object(condition, 'post_type'):
                condition.pop('post_type')
            list_posts = mongoDb.discovery_post.find(condition)
            list_posts = list(list_posts)

            if len(list_posts) > 0:
                total_stars = 0
                total_reviews = 0
                total_group_bookings = 0

                for post in list_posts:
                    if post['post_type'] == enums.post_review:
                        total_stars += post['stars']
                        total_reviews += 1
                    if post['post_type'] == enums.post_group_buying:
                        total_group_bookings += 1

                res['result'] = {
                    'average_stars': total_stars / total_reviews if total_reviews else 0,
                    'total_reviews': total_reviews,
                    'total_group_bookings': total_group_bookings,
                }

        return Response(res, status=status.HTTP_200_OK)


class GetDetailBubbleProfile(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get_profile(self, user_id: int):
        try:
            profile = Profile.objects.get(user=user_id)
            return {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
                'description': profile.description,
            }
        except Profile.DoesNotExist:
            return services.fake_user_profile

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'status': {
                '$in': [enums.status_active, enums.status_temporarily_closed, enums.status_requesting_delete]
            }
        })
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

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

        relationship = enums.relationship_self if post['creator'] == my_id else enums.relationship_not_know

        profile = Profile.objects.get(user=post['creator'])

        res = None

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
                reviewed_profile = self.get_profile(user_id)
                user_reviewed = {
                    'id': user_id,
                    'name': reviewed_profile['name'],
                    'avatar': reviewed_profile['avatar'],
                    'description': reviewed_profile['description'],
                    'location': reviewed_profile['location']
                }

            res = {
                'id': str(post['_id']),
                'postType': post['post_type'],
                'topic': post['topic'],
                'feeling': post['feeling'],
                'location': post['location'],
                'content': post['content'],
                'images': link_images,
                'stars': post['stars'],
                'userReviewed': user_reviewed,
                'link': post['link'],
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalSaved': post['total_saved'],
                'creator': post['creator'],
                'creatorName': profile.name,
                'creatorAvatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'created': str(post['created']),
                'isLiked': is_liked,
                'isSaved': is_saved,
                'relationship': relationship
            }

        elif post['post_type'] == enums.post_group_buying:
            status_joined = enums.status_not_joined
            deposit = None
            amount = None
            note = None
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

            request_update_price = None
            if post['creator'] == my_id:
                try:
                    user_request = User_Request.objects.get(type=enums.request_update_price, post_id=str(
                        post['_id']), creator=my_id, status=enums.status_active)
                    request_update_price = services.str_to_dict(
                        user_request.data)
                except User_Request.DoesNotExist:
                    pass

            res = {
                'id': str(post['_id']),
                'postType': post['post_type'],
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
                'creatorName': profile.name,
                'creatorAvatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'creatorLocation': profile.location,
                'created': str(post['created']),
                'isLiked': is_liked,
                'status': status_joined,
                'postStatus': post['status'],
                'relationship': relationship,
                'requestUpdatePrice': request_update_price,
            }

        return Response(res, status=status.HTTP_200_OK)


class GetListTopGroupBuying(GenericAPIView):
    permission_classes = [AllowAny, ]

    def get_info_creator(self, user_id):
        try:
            profile = Profile.objects.get(user=user_id)
            return {
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'location': profile.location,
            }
        except Profile.DoesNotExist:
            return {
                'name': '',
                'avatar': '',
                'location': ''
            }

    def check_liked_and_status_joined(self, user_id: int, post_id: str):
        if (user_id == None):
            return {
                'is_liked': True,
                'join': {
                    'deposit': None,
                    'amount': None,
                    'note': None,
                    'status': enums.status_not_joined,
                }
            }

        check_liked = mongoDb.reaction.find_one({
            'type': enums.react_post,
            'reacted_id': post_id,
            'creator': user_id,
            'status': enums.status_active
        })
        is_liked = bool(check_liked)

        status_joined = enums.status_not_joined
        deposit = None
        amount = None
        note = None
        check_joining = mongoDb.join_personal.find_one({
            'post_id': post_id,
            'creator': user_id,
            'status': enums.status_joined_not_bought
        })
        if check_joining:
            status_joined = check_joining['status']
            deposit = check_joining['money']
            amount = check_joining['amount']
            note = check_joining['note']

        return {
            'is_liked': is_liked,
            'join': {
                'deposit': deposit,
                'amount': amount,
                'note': note,
                'status': status_joined,
            }
        }

    def get(self, request):
        my_id = services.get_user_id_from_request(request)

        list_posts = mongoDb.discovery_post.aggregate([
            {
                '$match': {
                    'post_type': enums.post_group_buying,
                    'status': enums.status_active,
                }
            },
            {
                '$sort': {
                    'created': pymongo.DESCENDING,
                    'total_reacts': pymongo.DESCENDING,
                    'total_groups': pymongo.DESCENDING,
                }
            },
            {
                '$limit': 10
            }
        ])

        # This is for update all joining and joined, choose this api because it's called one time in app cycle
        now = services.get_datetime_now()
        list_joined_not_bought = mongoDb.join_personal.find({
            'creator': my_id,
            'status': enums.status_joined_not_bought
        })
        for joined in list_joined_not_bought:
            if joined['time_will_buy'] < now:
                mongoDb.join_personal.update_one(
                    {
                        "_id": joined['_id'],
                    },
                    {
                        '$set': {
                            'status': enums.status_joined_bought
                        }
                    }
                )
        # ------------------------

        res = []

        for post in list_posts:
            link_images = []
            for image in post['images']:
                temp = services.create_link_image(image)
                link_images.append(temp)

            info_creator = self.get_info_creator(user_id=post['creator'])

            check_liked_joined = self.check_liked_and_status_joined(
                user_id=my_id, post_id=str(post['_id']))

            is_liked = check_liked_joined['is_liked']
            join = check_liked_joined['join']

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            request_update_price = None
            if post['creator'] == my_id:
                try:
                    user_request = User_Request.objects.get(
                        creator=my_id, post_id=str(post['_id']), type=enums.request_update_price, status=enums.status_active)
                    data = services.str_to_dict(user_request.data)
                    request_update_price = {
                        'retailPrice': data['retail_price'],
                        'prices': data['prices']
                    }
                except User_Request.DoesNotExist:
                    pass

            temp = {
                'id': str(post['_id']),
                'postType': enums.post_group_buying,
                'topic': post['topic'],
                'content': post['content'],
                'images': link_images,
                'retailPrice': post['retail_price'],
                'prices': post['prices'],
                'deposit': join['deposit'],
                'amount': join['amount'],
                'note': join['note'],
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
                'status': join['status'],
                'postStatus': post['status'],
                'relationship': relationship,
                'requestUpdatePrice': request_update_price,
            }

            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)
