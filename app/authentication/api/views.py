from datetime import timedelta
from os import stat
from rest_framework_simplejwt.exceptions import TokenError
from authentication import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from authentication.api import serializers
from utilities.exception.exception_handler import CustomError
from utilities.exception import error_message, error_key
from utilities import enums
from utilities import services
from utilities import validate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from findme.mongo import mongoDb
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.permissions import IsAuthenticated
from utilities.disableObject import DisableObject


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
        # REQUEST OPEN ACCOUNT
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


# check_otp is also verify in register
class CheckOTP(GenericAPIView):
    def get_object(self, username, code):
        try:
            return models.VerifyCode.objects.get(username=username, code=code)
        except models.VerifyCode.DoesNotExist:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

    def post(self, request):
        username = request.data['username']
        code = int(request.data['code'])

        if (code == 0):
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        verify_code = self.get_object(username, code)
        verify_code.code = 0
        verify_code.save()

        return Response(None, status=status.HTTP_200_OK)


class Register(GenericAPIView):
    def check_user_existed(self, facebook, email, phone):
        try:
            if facebook:
                models.User.objects.get(facebook=facebook, is_active=1)
            elif email:
                models.User.objects.get(email=email, is_active=1)
            elif phone:
                models.User.objects.get(phone=phone, is_active=1)
            raise CustomError(error_message.username_existed,
                              error_key.username_existed)
        except models.User.DoesNotExist:
            pass

    def post(self, request):
        facebook = request.data['facebook']
        email = request.data['email']
        phone = request.data['phone']
        password = request.data['password']
        confirm_password = request.data['confirmPassword']

        # validate data
        if password != confirm_password:
            raise CustomError(error_message.password_not_match,
                              error_key.password_not_match)
        if not validate.validate_password(password):
            raise CustomError(error_message.password_invalid,
                              error_key.password_invalid)
        if facebook:
            pass
        elif email:
            if not validate.is_email_valid(email):
                raise CustomError()
        elif phone:
            if not validate.is_phone_valid(phone):
                raise CustomError()

        # check username existed
        self.check_user_existed(facebook, email, phone)

        # save user to database
        register_data = {
            'facebook': facebook,
            'email': email,
            'phone': phone,
            'password': password
        }
        serializer = serializers.RegisterSerializer(data=register_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(None, status=status.HTTP_200_OK)


class Login(GenericAPIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        # get object
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
            check = check_password(password, user.password)
            if not check:
                raise CustomError(error_message.login_fail,
                                  error_key.login_fail)
        except models.User.DoesNotExist:
            raise CustomError(error_message.login_fail, error_key.login_fail)

        # check is this user is temporary block
        try:
            # user temporary locking
            list_user_temporary_lock: list = DisableObject.get_disable_object(
                enums.disable_user)[enums.disable_user]
            list_user_temporary_lock.index(user.id)
            res = {
                'username': username,
                'isLocking': True,
            }
            return Response(res, status=status.HTTP_200_OK)
        except ValueError:
            # user is requesting delete account
            list_user_requesting_delete: list = DisableObject.get_disable_object(
                enums.disable_request_delete_account)[enums.disable_request_delete_account]
            for request in list_user_requesting_delete:
                if request['userId'] == user.id and request['isActive'] == True:
                    res = {
                        'username': username,
                        'isLocking': True,
                    }
                    return Response(res, status=status.HTTP_200_OK)

        # login success
        return Response(user.tokens(), status=status.HTTP_200_OK)


class Logout(GenericAPIView):
    def post(self, request):
        refreshToken = request.data['refreshToken']
        try:
            RefreshToken(refreshToken).blacklist()
        except TokenError:
            raise CustomError(error_message.token_blacklisted,
                              error_key.token_blacklisted)

        return Response(None, status=status.HTTP_200_OK)


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


class VerifyToken(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        id = services.get_user_id_from_request(request)
        return Response(id, status=status.HTTP_200_OK)


class MyRefreshToken(GenericAPIView):
    def post(self, request):
        refreshToken = request.data['refresh']
        try:
            refresh = RefreshToken(refreshToken)
        except TokenError:
            raise CustomError(error_message.token_blacklisted,
                              error_key.token_blacklisted)

        res = {
            'access': str(refresh.access_token)
        }
        return Response(res, status=status.HTTP_200_OK)


class GetIdEnjoyMode(GenericAPIView):
    def get(self, request):
        temp = mongoDb.userEnjoyMode.find_one_and_update(
            {},
            {
                '$inc': {
                    'numberUser': 1
                }
            }
        )
        res = '__{}'.format(abs(temp['numberUser'] + 1))
        return Response(res, status=status.HTTP_200_OK)


class LockAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        id = services.get_user_id_from_request(request)
        DisableObject.add_disable_object(enums.disable_user, id)
        return Response(None, status=status.HTTP_200_OK)


class OpenAccount(GenericAPIView):
    def put(self, request):
        username = request.data['username']
        verify_code = request.data['verifyCode']

        # verify
        try:
            user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
        except models.User.DoesNotExist:
            raise CustomError(error_message.username_not_exist,
                              error_key.username_not_exist)

        try:
            models.VerifyCode.objects.get(
                username=username, code=verify_code)
        except models.VerifyCode.DoesNotExist:
            raise CustomError(error_message.otp_invalid, error_key.otp_invalid)

        DisableObject.remove_disable_object(enums.disable_user, user.id)
        DisableObject.disable_request_delete_account(user.id)

        return Response(None, status=status.HTTP_200_OK)


class RequestDeleteAccount(GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        created_time = services.get_datetime_now()
        request_adding = {
            'userId': services.get_user_id_from_request(request),
            'createdTime': created_time,
            'deleteTime': created_time + timedelta(days=20),
            'isActive': True,
        }
        DisableObject.add_request_delete_account(request_adding)
        return Response(None, status=status.HTTP_200_OK)
