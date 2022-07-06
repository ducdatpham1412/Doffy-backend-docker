from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mysql import mysql_select, mysql_insert, mysql_update
from authentication.query.verify_code import SEARCH_OTP, INSERT_OTP, UPDATE_OTP


class Check(GenericAPIView):
    def get(self, request):
        check = mysql_update(UPDATE_OTP(username='what@gmail.com', code=1234))
        return Response(None, 200)
