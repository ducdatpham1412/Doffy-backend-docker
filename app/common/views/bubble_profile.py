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

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])
        list_topics = services.get_object(request.query_params, 'listTopics')

        condition = {
            'creator': {
                '$ne': my_id
            },
            'status': enums.status_active
        }
        if list_topics != None:
            condition['topic'] = {
                '$in': json.loads(list_topics)
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

            check_saved = mongoDb.save.find_one({
                'type': enums.save_post,
                'saved_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active,
            })
            is_saved = bool(check_saved)

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            res_posts.append({
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
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'isSaved': is_saved,
                'relationship': enums.relationship_not_know
            })

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
        listTopics = services.get_object(request.query_params, 'listTopics')

        condition = {
            'status': enums.status_active
        }
        if listTopics != None:
            condition['topic'] = {
                '$in': json.loads(listTopics)
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
            }

        res_posts = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                temp = services.create_link_image(image)
                link_images.append(temp)

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            res_posts.append({
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
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(post['created']),
                'isLiked': True,
                'isSaved': True,
                'relationship': enums.relationship_not_know
            })

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
