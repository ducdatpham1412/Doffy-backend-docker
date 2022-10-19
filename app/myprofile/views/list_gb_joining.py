from findme.mongo import mongoDb
from myprofile import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
from utilities.exception.exception_handler import CustomError
from utilities.renderers import PagingRenderer
from bson.objectid import ObjectId
import pymongo


class GetListGbJoining(GenericAPIView):
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

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_joining = mongoDb.join_group_buying.find({
            'creator': my_id,
            'status': {
                '$in': [enums.status_joined_not_bought]
            }
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1) * take)
        total_joined = mongoDb.join_group_buying.count({
            'creator': my_id,
            'status': {
                '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
            }
        })

        list_posts = []
        for joined in list_joining:
            post = mongoDb.discovery_post.find_one({
                '_id': ObjectId(joined['post_id']),
                'post_type': enums.post_group_buying,
                'status': enums.status_active
            })
            if post:
                list_posts.append(post)

        list_gb_joined = []
        for post in list_posts:
            link_images = []
            for image in post['images']:
                link_images.append(services.create_link_image(image))

            info_creator = self.get_creator_name_avatar(
                user_id=post['creator'])

            check_liked = mongoDb.reaction.find_one({
                'type': enums.react_post,
                'reacted_id': str(post['_id']),
                'creator': my_id,
                'status': enums.status_active
            })
            is_liked = bool(check_liked)

            relationship = enums.relationship_self if post[
                'creator'] == my_id else enums.relationship_not_know

            check_joined = mongoDb.join_group_buying.find_one({
                'post_id': str(post['_id']),
                'creator': my_id,
                'status': {
                    '$in': [enums.status_joined_not_bought, enums.status_joined_bought]
                }
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
                'deadlineDate': str(post['deadline_date']),
                'startDate': str(post['start_date']),
                'endDate': str(post['end_date']),
                'creator': post['creator'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'creatorLocation': info_creator['location'],
                'created': str(post['created']),
                'isLiked': is_liked,
                'status': status_joined,
                'relationship': relationship,
            }
            list_gb_joined.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_joined,
            'data': list_gb_joined,
        }

        return Response(res, status=status.HTTP_200_OK)
