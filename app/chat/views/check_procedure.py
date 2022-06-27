from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mysql import query_mysql, call_procedure


class CheckProcedure(GenericAPIView):

    def get(self, request):
        list_user = call_procedure('hello', [2])

        res = []
        for user in list_user:
            temp = {
                **user,
                'date_joined': str(user['date_joined'])
            }
            res.append(temp)

        return Response(res, status=200)
