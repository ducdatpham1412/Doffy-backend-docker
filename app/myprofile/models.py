from django.db import models
from authentication.models import User
from utilities import enums, services
from datetime import datetime


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', primary_key=True, editable=False
    )
    name = models.CharField(max_length=enums.NAME_MAX_LENGTH,
                            default=enums.NAME_DEFAULT)
    anonymous_name = models.CharField(
        max_length=enums.NAME_MAX_LENGTH, default=services.init_name_profile())
    description = models.TextField(
        default=enums.string_not_specify, max_length=enums.DESCRIPTION_MAX_LENGTH)
    avatar = models.TextField(default=enums.AVATAR_DEFAULT)
    cover = models.TextField(default='')
    followers = models.IntegerField(default=0)
    followings = models.IntegerField(default=0)
    location = models.TextField(default='')


class Follow(models.Model):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followed')


class PurchaseHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='purchase_history', editable=False
    )
    money = models.CharField(max_length=10, editable=False)
    created = models.DateTimeField(default=datetime.now, editable=False)
    status = models.IntegerField(default=enums.status_active)


class ErrorLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='error_log', editable=False
    )
    error = models.TextField(editable=False)
    created = models.DateTimeField(default=datetime.now, editable=False)
