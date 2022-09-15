from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication.serializers import RegisterSerializer


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        register_data = {
            'email': 'how@doffy.vn',
            'phone': '',
            'password': ''
        }

        serializer = RegisterSerializer(data=register_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        print('user is: ', user)

        return Response(None, status=200)
