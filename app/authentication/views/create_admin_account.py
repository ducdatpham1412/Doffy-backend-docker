from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework import status
from utilities import validate
from authentication import serializers
from utilities.services import get_user_id_from_request
from utilities.enums import account_admin
from django.db.models import Q


class RegisterAdmin(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def check_user_existed(self, email, phone):
        try:
            count = models.User.objects.filter(Q(email=email) | Q(phone=phone))
            if len(count) > 0:
                raise CustomError(error_message.username_existed,
                                  error_key.username_existed)
        except models.User.DoesNotExist:
            pass

    def post(self, request):
        email = request.data['email']
        phone = request.data['phone']
        password = request.data['password']
        confirm_password = request.data['confirmPassword']

        self.check_user_existed(email=email, phone=phone)

        if password != confirm_password:
            raise CustomError(error_message.password_not_match,
                              error_key.password_not_match)
        if not validate.validate_password(password):
            raise CustomError(error_message.password_invalid,
                              error_key.password_invalid)

        if email:
            if not validate.is_email_valid(email):
                raise CustomError()
        elif phone:
            if not validate.is_phone_valid(phone):
                raise CustomError()

        my_id = get_user_id_from_request(request)
        doffy_code = request.headers['doffycode']
        if my_id != 1 or doffy_code != 'doffy xin chao':
            raise CustomError()

        register_data = {
            'email': email,
            'phone': phone,
            'password': password,
            'account_type': account_admin,
        }
        serializer = serializers.RegisterSerializer(data=register_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(None, status=status.HTTP_200_OK)
