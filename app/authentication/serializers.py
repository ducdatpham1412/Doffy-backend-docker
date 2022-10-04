from authentication import models
import myprofile.models
from rest_framework import serializers
from setting.models import Extend, Information
from django.contrib.auth.hashers import make_password
from findme.mysql import mysql_select, mysql_insert, mysql_update
from authentication.query import verify_code


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)

    class Meta:
        model = models.User
        fields = '__all__'


class RequestOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VerifyCode
        fields = '__all__'

    def create(self, validated_data):
        username = validated_data['username']
        code = validated_data['code']

        code_find = mysql_select(verify_code.SEARCH_OTP(username=username))
        if code_find:
            mysql_update(verify_code.UPDATE_OTP(username=username, code=code))
        else:
            mysql_insert(verify_code.INSERT_OTP(username=username, code=code))

        return {}


# REGISTER
class RegisterSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField(required=False, allow_blank=True)
    # phone = serializers.CharField(required=False, allow_blank=True)
    # password = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.User
        fields = ['email', 'phone', 'password', 'account_type']

    def create(self, validated_data):
        temp_password = validated_data.pop('password')
        if temp_password:
            encrypt_password = make_password(temp_password)
        else:
            encrypt_password = ''

        user = models.User.objects.create(
            **validated_data, password=encrypt_password)
        Information.objects.create(user=user)
        myprofile.models.Profile.objects.create(user=user)
        Extend.objects.create(user=user)

        return user


class RequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User_Request
        fields = '__all__'
