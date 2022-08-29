from rest_framework.generics import GenericAPIView
from findme.mongo import mongoDb
from rest_framework.response import Response
from rest_framework import status


class GetIdEnjoyMode(GenericAPIView):
    def get(self, request):
        temp = mongoDb.user_enjoy.find_one_and_update(
            {},
            {
                '$inc': {
                    'number_users': 1
                }
            }
        )
        res = '__{}'.format(abs(temp['number_users'] + 1))
        return Response(res, status=status.HTTP_200_OK)
