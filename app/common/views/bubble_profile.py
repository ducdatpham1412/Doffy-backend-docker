from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from myprofile.models import Profile
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
import pymongo
from bson.objectid import ObjectId
import json
from utilities.renderers import PagingRenderer


class GetListBubbleProfile(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
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

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])
        list_topics = services.get_object(request.query_params, 'topics')

        services.get_list_user_block(user_id=my_id)

        list_user_not_in = [my_id]
        list_user_not_in.extend(services.get_list_user_block(my_id))
        condition = {
            'creator': {
                '$nin': list_user_not_in,
            },
            'status': enums.status_active
        }
        if list_topics != None or services.get_len(list_topics) > 0:
            condition['topic'] = {
                '$all': json.loads(list_topics)
            }

        total_posts = mongoDb.discovery_post.count(condition)

        list_posts = mongoDb.discovery_post.find(condition).sort(
            [('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
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

            check_liked = mongoDb.reaction.find_one({
                'type': enums.react_post,
                'reacted_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active
            })
            is_liked = bool(check_liked)

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            # post review
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
                if post['end_date'] < services.get_datetime_now():
                    continue

                check_joined = mongoDb.join_group_buying.find_one({
                    'post_id': str(post['_id']),
                    'creator': my_id,
                    'status': {
                        '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
                    },
                })
                status_joined = enums.status_not_joined
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
                    'startDate': str(post['start_date']),
                    'endDate': str(post['end_date']),
                    'creator': post['creator'],
                    'creatorName': info_creator['name'],
                    'creatorAvatar': info_creator['avatar'],
                    'creatorLocation': info_creator['location'],
                    'created': str(post['created']),
                    'isLiked': is_liked,
                    'status': status_joined,
                    'relationship': enums.relationship_not_know,
                }
                res_posts.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': res_posts,
        }

        return Response(res, status=status.HTTP_200_OK)


class GetListBubbleProfileOfUserEnjoy(GenericAPIView):
    renderer_classes = [PagingRenderer, ]

    def filter_list_user_id(self, list_posts: list):
        result = []
        for post in list_posts:
            try:
                result.index(post['creator'])
            except ValueError:
                result.append(post['creator'])
        return result

    def get(self, request):
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])
        list_topics = services.get_object(request.query_params, 'topics')

        condition = {
            'status': enums.status_active
        }
        if list_topics != None or services.get_len(list_topics) > 0:
            condition['topic'] = {
                '$all': json.loads(list_topics)
            }

        total_posts = mongoDb.discovery_post.count(condition)

        list_posts = mongoDb.discovery_post.find(condition).sort(
            [('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
        list_posts = list(list_posts)

        id_name_avatar_object = {}
        for user_id in self.filter_list_user_id(list_posts):
            profile = Profile.objects.get(user=user_id)
            id_name_avatar_object['{}'.format(user_id)] = {
                'id': user_id,
                'name': profile.name,
                'avatar': services.create_link_image(profile.avatar),
                'location': profile.location,
            }

        res_posts = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                temp = services.create_link_image(image)
                link_images.append(temp)

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            if post['post_type'] == enums.post_review:
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
                    'totalLikes': post['total_reacts'],
                    'totalComments': post['total_comments'],
                    'totalSaved': post['total_saved'],
                    'creator': post['creator'],
                    'creatorName': info_creator['name'],
                    'creatorAvatar': info_creator['avatar'],
                    'created': str(post['created']),
                    'isLiked': True,
                    'isSaved': True,
                    'relationship': enums.relationship_not_know
                })

            elif post['post_type'] == enums.post_group_buying:
                if post['end_date'] < services.get_datetime_now():
                    continue

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
                    'startDate': str(post['start_date']),
                    'endDate': str(post['end_date']),
                    'creator': post['creator'],
                    'creatorName': info_creator['name'],
                    'creatorAvatar': info_creator['avatar'],
                    'creatorLocation': info_creator['location'],
                    'created': str(post['created']),
                    'isLiked': True,
                    'status': enums.status_not_joined,
                    'relationship': enums.relationship_not_know,
                }
                res_posts.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': res_posts,
        }

        return Response(res, status=status.HTTP_200_OK)


class GetDetailBubbleProfile(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)

        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'status': enums.status_active
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

        check_saved = mongoDb.save.find_one({
            'type': enums.save_post,
            'saved_id': str(post['_id']),
            'creator': my_id,
            'status': enums.status_active,
        })
        is_saved = bool(check_saved)

        is_my_post = post['creator'] == my_id
        relationship = enums.relationship_self if is_my_post else enums.relationship_not_know

        profile = Profile.objects.get(user=post['creator'])

        res = {
            'id': str(post['_id']),
            'topic': post['topic'],
            'feeling': post['feeling'],
            'location': post['location'],
            'content': post['content'],
            'images': link_images,
            'stars': post['stars'],
            'link': post['link'],
            'totalLikes': post['total_reacts'],
            'totalComments': post['total_comments'],
            'totalSaved': post['total_saved'],
            'creator': post['creator'],
            'creatorName': profile.name,
            'creatorAvatar': services.create_link_image(profile.avatar),
            'created': str(post['created']),
            'isLiked': is_liked,
            'isSaved': is_saved,
            'relationship': relationship
        }

        return Response(res, status=status.HTTP_200_OK)


class GetDetailBubbleProfileEnjoy(GenericAPIView):
    def get(self, request, post_id):
        post = mongoDb.discovery_post.find_one({
            '_id': ObjectId(post_id),
            'status': enums.status_active
        })
        if not post:
            raise CustomError(error_message.post_not_existed,
                              error_key.post_not_existed)

        link_images = []
        for image in post['images']:
            link_images.append(services.create_link_image(image))

        is_liked = True

        profile = Profile.objects.get(user=post['creator'])

        res = {
            'id': str(post['_id']),
            'topic': post['topic'],
            'feeling': post['feeling'],
            'location': post['location'],
            'content': post['content'],
            'images': link_images,
            'stars': post['stars'],
            'link': post['link'],
            'totalLikes': post['total_reacts'],
            'totalComments': post['total_comments'],
            'totalSaved': post['total_saved'],
            'creator': post['creator'],
            'creatorName': profile.name,
            'creatorAvatar': services.create_link_image(profile.avatar),
            'created': str(post['created']),
            'isLiked': is_liked,
            'isSaved': True,
            'relationship': enums.relationship_not_know,
        }

        return Response(res, status=status.HTTP_200_OK)
