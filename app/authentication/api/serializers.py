from authentication import models
from myprofile.models import Profile
from rest_framework import serializers
from setting.models import Extend, Information
from utilities.exception import error_key, error_message
from utilities.exception.exception_handler import CustomError
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from findme.mongo import mongoDb


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

        try:
            code_find = models.VerifyCode.objects.get(username=username)

            code_find.username = username
            code_find.code = code
            code_find.save()
            return code_find
        except models.VerifyCode.DoesNotExist:
            return models.VerifyCode.objects.create(**validated_data)


# REGISTER
class RegisterSerializer(serializers.ModelSerializer):
    facebook = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField()

    class Meta:
        model = models.User
        fields = ['facebook', 'email', 'phone', 'password']

    def create(self, validated_data):
        encrypt_password = make_password(validated_data.pop('password'))
        user = models.User.objects.create(
            **validated_data, password=encrypt_password)
        Information.objects.create(user=user)
        Profile.objects.create(user=user)
        Extend.objects.create(user=user)
        mongoDb.analysis.find_one_and_update(
            {
                'type': 'checkHadKnowEachOther'
            },
            {
                '$set': {
                    'data.{}'.format(user.id): []
                }
            }
        )
        mongoDb.notification.insert_one({
            'userId': user.id,
            'list': []
        })

        return user


# LOGIN
class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    tokens = serializers.SerializerMethodField()

    check_user: any

    def get_object(self, username, password):
        try:
            self.check_user = models.User.objects.get(
                Q(email=username) | Q(phone=username), is_active=1)
            check = check_password(password, self.check_user.password)
            if not check:
                raise CustomError(error_message.login_fail,
                                  error_key.login_fail)
        except models.User.DoesNotExist:
            raise CustomError(error_message.login_fail,
                              error_key.login_fail)

    def get_tokens(self, obj):
        return {
            'token': self.check_user.tokens()['token'],
            'refreshToken': self.check_user.tokens()['refreshToken']
        }

    class Meta:
        model = models.User
        fields = ['username', 'password', 'tokens']

    def validate(self, attrs):
        username = attrs.get('username', '')
        password = attrs.get('password', '')

        if not username or not password:
            raise CustomError(error_message.login_fail, error_key.login_fail)
        self.get_object(username, password)

        return attrs
