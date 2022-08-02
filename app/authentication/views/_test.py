from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from findme.mysql import mysql_select
from authentication.query.user import SEARCH_USERNAME
from setting.models import Block


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        temp = Block.objects.all().delete()

        return Response(None, status=200)
