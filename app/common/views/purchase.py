from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication


class CreatePurchase(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        return Response(None, status=status.HTTP_200_OK)


class ConfirmPurchase(GenericAPIView):
    permission_classes = [AllowAny, ]

    def get(self, request):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjY5MDMwMDI3LCJpYXQiOjE2Njc0NDU3MzIsImp0aSI6IjhkMDVmMGI0MTBkNTRmZjViNzlkNDliMmU2YmIwNzVlIiwidXNlcl9pZCI6MX0.XakvxVVObx2emldvIJte8C0VFZsVYOG9rRF58UXs9OY00000"

        # This method have been researched and confirmed it's true
        check = JWTAuthentication().get_validated_token(raw_token=token)

        print('check is: ', check)

        return Response(None, status=status.HTTP_200_OK)
