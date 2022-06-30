from rest_framework.generics import GenericAPIView
from findme.mongo import mongoDb
from rest_framework.response import Response
from rest_framework import status


class GetIdEnjoyMode(GenericAPIView):
    def get(self, request):
        temp = mongoDb.userEnjoyMode.find_one_and_update(
            {},
            {
                '$inc': {
                    'numberUser': 1
                }
            }
        )
        res = '__{}'.format(abs(temp['numberUser'] + 1))
        return Response(res, status=status.HTTP_200_OK)
