from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mysql import mysql_select, mysql_insert, mysql_update
from authentication.query.verify_code import SEARCH_OTP, INSERT_OTP, UPDATE_OTP
from authentication.query.user import SEARCH_USERNAME


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        username = request.data.get('username', None)
        res = mysql_select(SEARCH_USERNAME(username=username))[0]

        return Response(username, status=200)
