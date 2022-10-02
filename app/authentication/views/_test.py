from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication.models import User_Request
from authentication.serializers import RequestUserSerializer
from django.db.models import Q


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        list_requests = User_Request.objects.filter(~Q(creator=2))
        serializer = RequestUserSerializer(list_requests, many=True)

        return Response(serializer.data, status=200)
