from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication import models
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from rest_framework import status
from utilities import validate
from authentication import serializers


class Register(GenericAPIView):
    def check_user_existed(self, email, phone):
        try:
            if email:
                models.User.objects.get(email=email, is_active=1)
            elif phone:
                models.User.objects.get(phone=phone, is_active=1)
            raise CustomError(error_message.username_existed,
                              error_key.username_existed)
        except models.User.DoesNotExist:
            pass

    def check_otp(self, username, code):
        try:
            verify_code = models.VerifyCode.objects.get(
                username=username, code=code)
            verify_code.code = 0
            verify_code.save()
        except models.VerifyCode.DoesNotExist:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

    def post(self, request):
        email = request.data['email']
        phone = request.data['phone']
        password = request.data['password']
        confirm_password = request.data['confirmPassword']
        code = request.data['code']

        # check username existed
        self.check_user_existed(email=email, phone=phone)

        # validate password
        if password != confirm_password:
            raise CustomError(error_message.password_not_match,
                              error_key.password_not_match)
        if not validate.validate_password(password):
            raise CustomError(error_message.password_invalid,
                              error_key.password_invalid)

        # check otp
        if email:
            if not validate.is_email_valid(email):
                raise CustomError()
            self.check_otp(username=email, code=code)
        elif phone:
            if not validate.is_phone_valid(phone):
                raise CustomError()
            self.check_otp(username=phone, code=code)

        # save user to database
        register_data = {
            'email': email,
            'phone': phone,
            'password': password
        }
        serializer = serializers.RegisterSerializer(data=register_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(user.tokens(), status=status.HTTP_200_OK)
