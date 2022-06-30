from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utilities.exception.exception_handler import CustomError
from django.db.models import Q
from utilities.exception import error_message, error_key
from authentication import models
from utilities import validate
from django.contrib.auth.hashers import make_password


class ResetPassword(GenericAPIView):
    def get_object(self, username):
        try:
            return models.User.objects.get(Q(email=username) | Q(phone=username))
        except models.User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

    def put(self, request):
        username = request.data['username']
        newPassword = request.data['newPassword']
        confirmPassword = request.data['confirmPassword']

        # check confirm password
        if not validate.validate_password(newPassword):
            raise CustomError(error_message.password_invalid,
                              error_key.password_invalid)
        if (confirmPassword != newPassword):
            raise CustomError(error_message.password_not_match,
                              error_key.password_not_match)

        # check verify code
        user = self.get_object(username)
        user.password = make_password(newPassword)
        user.save()
        return Response(None, status=status.HTTP_200_OK)
