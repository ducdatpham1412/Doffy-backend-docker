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

        list_joining = mongoDb.join_personal.aggregate([
            {
                '$match': {
                    'creator': my_id,
                    'status': enums.status_joined_not_bought,
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

        total_joined = mongoDb.join_personal.count({
            'creator': my_id,
            'status': enums.status_joined_not_bought
        })

        list_gb_joining = []
        for joining in list_joining:
            post = mongoDb.discovery_post.find_one({
                '_id': ObjectId(joining['post_id']),
                'post_type': enums.post_group_buying,
                'status': {
                    '$in': [enums.status_active, enums.status_temporarily_closed,  enums.status_requesting_delete]
                }
            })
            if post:
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

                temp = {
                    'id': str(post['_id']),
                    'joinId': str(joining['_id']),
                    'postType': enums.post_group_buying,
                    'topic': post['topic'],
                    'content': post['content'],
                    'images': link_images,
                    'retailPrice': post['retail_price'],
                    'prices': post['prices'],
                    'deposit': joining['money'],
                    'amount': joining['amount'],
                    'note': joining['note'],
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
                    'status': enums.status_joined_not_bought,
                    'postStatus': post['status'],
                    'relationship': relationship,
                    'requestUpdatePrice': None,
                }
                list_gb_joining.append(temp)

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_joined,
            'data': list_gb_joining,
        }

        return Response(res, status=status.HTTP_200_OK)
