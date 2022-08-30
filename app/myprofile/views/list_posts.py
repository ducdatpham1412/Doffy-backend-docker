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


class GetListPost(GenericAPIView):
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
            'status': {
                '$in': status_scope
            }
        }).sort(sort_condition).limit(take).skip((page_index-1)*take)
        total_posts = mongoDb.discovery_post.count({
            'creator': user_id,
            'status': {
                '$in': status_scope
            }
        })

        res_posts = []
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

            check_saved = mongoDb.save.find_one({
                'type': enums.save_post,
                'saved_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active,
            })
            is_saved = bool(check_saved)

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
                'isDraft': post['status'] == enums.status_draft,
                'relationship': relationship,
            }

            res_posts.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_posts,
            'data': res_posts
        }

        return Response(res, status=status.HTTP_200_OK)
