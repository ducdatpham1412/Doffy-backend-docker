from utilities.renderers import PagingRenderer
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities.renderers import PagingRenderer
from utilities import services
from findme.mongo import mongoDb
from utilities import enums
import pymongo
from myprofile.models import Profile
from setting.models import Block
from myprofile.models import Follow
from django.db.models import Q


class GetListPeopleLike(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    renderer_classes = [PagingRenderer, ]

    def filter_list_user_id(self, list_reacts: list):
        result = []
        for react in list_reacts:
            try:
                result.index(react['creator'])
            except ValueError:
                result.append(react['creator'])
        return result

    def get_relationship(self, my_id, your_id):
        if (my_id == your_id):
            return enums.relationship_self

        try:
            Block.objects.get(Q(block=my_id, blocked=your_id)
                              | Q(block=your_id, blocked=my_id))
            return enums.relationship_block
        except Block.DoesNotExist:
            pass

        try:
            Follow.objects.get(follower=my_id, followed=your_id)
            return enums.relationship_following
        except Follow.DoesNotExist:
            return enums.relationship_not_following

    def get(self, request, post_id):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])
        type = int(request.query_params['type'])

        list_reacts = mongoDb.reaction.find({
            'type': type,
            'reacted_id': post_id,
            'status': enums.status_active,
        }).sort([('created', pymongo.DESCENDING)]).limit(take).skip((page_index-1)*take)
        list_reacts = list(list_reacts)
        total_reacts = mongoDb.reaction.count({
            'type': type,
            'reacted_id': post_id,
            'status': enums.status_active,
        })

        id_name_avatar_object = {}
        for user_id in self.filter_list_user_id(list_reacts):
            relationship = self.get_relationship(my_id=my_id, your_id=user_id)
            if relationship == enums.relationship_block:
                id_name_avatar_object['{}'.format(user_id)] = {
                    'id': None,
                    'name': 'User',
                    'avatar': '',
                    'relationship': relationship,
                }
            else:
                profile = Profile.objects.get(user=user_id)
                id_name_avatar_object['{}'.format(user_id)] = {
                    'id': user_id,
                    'name': profile.name,
                    'avatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                    'relationship': relationship,
                }

        res_reacts = []
        for react in list_reacts:
            info_creator = id_name_avatar_object['{}'.format(react['creator'])]
            res_reacts.append({
                'id': str(react['_id']),
                'creator': info_creator['id'],
                'creatorName': info_creator['name'],
                'creatorAvatar': info_creator['avatar'],
                'created': str(react['created']),
                'relationship': info_creator['relationship'],
            })

        res = {
            'take': take,
            'pageIndex': page_index,
            'totalItems': total_reacts,
            'data': res_reacts,
        }

        return Response(res, status=status.HTTP_200_OK)
