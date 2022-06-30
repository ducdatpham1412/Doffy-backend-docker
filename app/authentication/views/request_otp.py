from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication import serializers
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums
from utilities import services
from utilities import validate


class RequestOTP(GenericAPIView):
    # REQUEST USE FOR BOTH THREES:
    #  0. register
    #  1. reset_password
    #  2. change_info
    #  4. request open account
    def check_email_exist(self, email):
        try:
            models.User.objects.get(email=email)
            raise CustomError(error_message.email_existed,
                              error_key.email_existed)
        except models.User.DoesNotExist:
            if validate.is_email_valid(email):
                return True
            raise CustomError()

    def check_phone_exist(self, phone):
        try:
            models.User.objects.get(phone=phone)
            raise CustomError(error_message.phone_existed,
                              error_key.phone_existed)
        except models.User.DoesNotExist:
            if validate.is_phone_valid(phone):
                return True
            raise CustomError()

    def get_object(self, username):
        try:
            models.User.objects.get(email=username)
            return 'email'
        except models.User.DoesNotExist:
            try:
                models.User.objects.get(phone=username)
                return 'phone'
            except models.User.DoesNotExist:
                raise CustomError(error_message.username_not_exist,
                                  error_key.username_not_exist)

    def post(self, request):
        username = request.data['username']
        type_otp = request.data['typeOTP']

        """
        REGISTER
        """
        if (type_otp == enums.type_otp_register):
            target_info = request.data['targetInfo']
            # check password and confirm_password
            password = request.data['password']
            confirm_password = request.data['confirmPassword']

            if (password != confirm_password):
                raise CustomError(error_message.password_not_match,
                                  error_key.password_not_match)

            # validate
            if (target_info == enums.target_info_email):
                self.check_email_exist(username)
            elif (target_info == enums.target_info_phone):
                self.check_phone_exist(username)

            # send verify_code
            verify_code = {
                'username': username,
                'code': services.get_randomCode(4)
            }
            serializer = serializers.RequestOTPSerializer(data=verify_code)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if target_info == enums.target_info_email:
                services.send_to_mail(username, verify_code['code'])
            elif target_info == enums.target_info_phone:
                print('send otp to phone: ', username)

            return Response(None, status=status.HTTP_200_OK)

        #
        # RESET_PASSWORD
        #
        elif (type_otp == enums.type_otp_reset_password):
            # check username valid
            if not(validate.is_email_valid(username) or validate.is_phone_valid(username)):
                raise CustomError()

            # check username is_exist and is_email or is_phone
            target = self.get_object(username)

            # send code to destination
            verify_code = {
                'username': username,
                'code': services.get_randomCode(4)
            }
            serializer = serializers.RequestOTPSerializer(
                data=verify_code)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if target == 'email':
                services.send_to_mail(username, verify_code['code'])
            elif target == 'phone':
                print('send otp to phone: ', username)

            return Response(None, status=status.HTTP_200_OK)

        #
        # CHANGE INFORMATION: email or phone
        #
        elif (type_otp == enums.type_otp_change_info):
            target_info = request.data['targetInfo']

            if target_info == enums.target_info_email:
                self.check_email_exist(username)
            elif target_info == enums.target_info_phone:
                self.check_phone_exist(username)

            # send verify code to new email
            verify_code = {
                'username': username,
                'code': services.get_randomCode(4)
            }
            serializer = serializers.RequestOTPSerializer(data=verify_code)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if target_info == enums.target_info_email:
                services.send_to_mail(username, verify_code['code'])
            elif target_info == enums.target_info_phone:
                print('send otp to phone: ', username)

            return Response(None, status=status.HTTP_200_OK)

        #
        # Request open account
        #
        elif (type_otp == enums.type_otp_request_open_account):
            verify_code = {
                'username': username,
                'code': services.get_randomCode(4)
            }
            serializer = serializers.RequestOTPSerializer(data=verify_code)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            services.send_to_mail(username, verify_code['code'])

            return Response(None, status=status.HTTP_200_OK)

        # NOT THING
        raise CustomError()
