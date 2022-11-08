from django.db import models
from django.contrib.auth.models import AbstractUser
from utilities import enums
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime


class User(AbstractUser):
    username = None
    is_superuser = None
    is_staff = None
    first_name = None
    last_name = None
    groups = None
    user_permissions = None
    account_type = models.SmallIntegerField(default=enums.account_user)
    bank_code = models.CharField(default='', max_length=10)
    bank_account = models.CharField(default='', max_length=20)

    email = models.EmailField(default='',)
    phone = models.CharField(default='', max_length=enums.PHONE_MAX_LENGTH)
    password = models.CharField(max_length=enums.PASSWORD_MAX_LENGTH)

    USERNAME_FIELD = 'id'

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'token': str(refresh.access_token),
            'refreshToken': str(refresh)
        }


class VerifyCode(models.Model):
    username = models.TextField()
    # type = models.SmallIntegerField()
    code = models.SmallIntegerField()
    # created = models.DateTimeField()

    def __str__(self):
        return str(self.code)


class User_Request(models.Model):
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_request', editable=False
    )
    type = models.IntegerField(editable=False)
    created = models.DateTimeField(default=datetime.now, )
    expired = models.DateTimeField()
    post_id = models.TextField(default='')
    data = models.TextField(default='')
    status = models.IntegerField(default=enums.status_active)
