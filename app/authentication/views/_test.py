from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from myprofile.models import PurchaseHistory


class Check(GenericAPIView):
    def get(self, request):
        return Response(None, status=200)

    def post(self, request):
        temp = PurchaseHistory.objects.get(user=1, post_id='')
        print('hihi: ', temp.money)
        return Response(temp.money, status=200)
