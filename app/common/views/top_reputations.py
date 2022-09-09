from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
import pymongo
from utilities import enums
from myprofile.models import Profile


class GetListTopReputation(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        my_id = services.get_user_id_from_request(request)

        list_reputations = mongoDb.total_items.find({
            'type': enums.total_reputation,
        }).sort([('value', pymongo.DESCENDING)])
        list_reputations = list(list_reputations)
        top_ten = list_reputations[0:9]

        list_top = []
        for reputation in top_ten:
            if reputation['value'] == 0:
                break
            profile = Profile.objects.get(user=reputation['user_id'])
            temp = {
                'id': str(reputation['_id']),
                'creator': reputation['user_id'],
                'creatorName': profile.name,
                'creatorAvatar': services.create_link_image(profile.avatar) if profile.avatar else '',
                'description': profile.description,
                'reputation': reputation['value']
            }
            list_top.append(temp)

        my_index = 0
        for index, reputation in enumerate(list_reputations):
            if reputation['user_id'] == my_id:
                my_index = index + 1

        res = {
            'list': list_top,
            'myIndex': my_index
        }

        return Response(res, status=status.HTTP_200_OK)
