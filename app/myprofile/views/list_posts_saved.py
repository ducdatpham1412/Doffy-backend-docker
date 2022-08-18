from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
import pymongo
from bson.objectid import ObjectId
from myprofile.models import Profile
from utilities.renderers import PagingRenderer


class GetListPostsSaved(GenericAPIView):
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

        list_saves = mongoDb.save.find({
            'type': enums.react_post,
            'creator': my_id,
            'status': enums.status_active
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        total_posts_saved = mongoDb.save.count({
            'type': enums.react_post,
            'creator': my_id,
            'status': enums.status_active,
        })

        list_posts = []
        for save in list_saves:
            post = mongoDb.discovery_post.find_one({
                '_id': ObjectId(save['saved_id']),
                'status': enums.status_active,
            })
            if post:
                list_posts.append(post)

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
                link_images.append(services.create_link_image(image))

            info_creator = id_name_avatar_object['{}'.format(post['creator'])]

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            temp = {
                'id': str(post['_id']),
                'topic': post['topic'],
                'feeling': post['feeling'],
                'location': post['location'],
                'content': post['content'],
                'images': link_images,
                'stars': post['stars'],
                'totalLikes': post['total_reacts'],
                'totalComments': post['total_comments'],
                'totalSaved': post['total_saved'],
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(post['created']),
                'isLiked': True,
                'isSaved': True,
                'relationship': relationship,
            }

            res_posts.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts_saved,
            'data': res_posts
        }

        return Response(res, status=status.HTTP_200_OK)