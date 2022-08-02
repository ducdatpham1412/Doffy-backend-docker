from common import models
from common import serializers
from findme.mongo import mongoDb
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


class GetResource(GenericAPIView):
    # permission_classes = [IsAuthenticated]
    def get_list_hobbies(self):
        query = models.Hobby.objects.all()
        list_hobbies = serializers.HobbySerializer(query, many=True).data
        return list_hobbies

    def get(self, request):
        mongo_resource = mongoDb.resource.find()
        image_background = mongo_resource[0]['imageBackground']
        gradient = mongo_resource[1]['gradient']
        listHobbies = mongo_resource[2]['listHobbies']

        res = {
            'listHobbies': listHobbies,
            'imageBackground': image_background,
            'gradient': gradient
        }

        return Response(res, status=status.HTTP_200_OK)
