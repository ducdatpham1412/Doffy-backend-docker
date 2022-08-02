from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import enums, services
import pymongo


class GetListBubbleGroup(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_groups = mongoDb.profilePostGroup.find().sort(
            [('createdTime', pymongo.DESCENDING)]).limit(take).skip((page_index - 1) * take)

        res = []
        for group in list_groups:
            relationship = enums.group_relationship_not_joined

            if my_id == group['creatorId']:
                relationship = enums.group_relationship_self
            elif services.check_include(group['listMembers'], my_id):
                relationship = enums.group_relationship_joined

            temp = {
                'id': str(group['_id']),
                'content': group['content'],
                'images': [services.create_link_image(group['images'][0])],
                'chatTagId': group['chatTagId'],
                'creatorId': group['creatorId'],
                'createdTime': str(group['createdTime']),
                'color': str(group['color']),
                'name': str(group['name']),
                'relationship': relationship
            }

            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)


class GetListBubbleGroupOfUserEnjoy(GenericAPIView):
    def get(self, request):
        take = int(request.query_params['take'])
        page_index = int(request.query_params['pageIndex'])

        list_groups = mongoDb.profilePostGroup.find().sort(
            [('createdTime', pymongo.DESCENDING)]).limit(take).skip((page_index - 1) * take)

        res = []
        for group in list_groups:
            temp = {
                'id': str(group['_id']),
                'content': group['content'],
                'images': [services.create_link_image(group['images'][0])],
                'chatTagId': group['chatTagId'],
                'creatorId': group['creatorId'],
                'createdTime': str(group['createdTime']),
                'color': str(group['color']),
                'name': str(group['name']),
                'relationship': enums.group_relationship_not_joined
            }
            res.append(temp)

        return Response(res, status=status.HTTP_200_OK)
