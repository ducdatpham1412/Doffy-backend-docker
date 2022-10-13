from myprofile.models import PurchaseHistory
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utilities import services
from authentication.models import User


class CreatePurchaseHistory(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        my_id = services.get_user_id_from_request(request)
        money = str(request.data['money'])

        user = User.objects.get(id=my_id)
        purchase = PurchaseHistory(user=user, money=money)
        purchase.save()

        return Response(None, status=status.HTTP_200_OK)
