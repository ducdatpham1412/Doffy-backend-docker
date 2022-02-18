from django.db import models
from django.contrib.auth.models import AbstractUser
from utilities import enums
from rest_framework_simplejwt.tokens import RefreshToken


class User(AbstractUser):
    username = None
    is_superuser = None
    is_staff = None
    first_name = None
    last_name = None
    groups = None
    user_permissions = None

    facebook = models.CharField(default='', max_length=200)
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

    def __str__(self):
        return str(self.code)
