from django.db import models
from authentication.models import User
from utilities import enums


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', primary_key=True, editable=False
    )
    name = models.CharField(max_length=enums.NAME_MAX_LENGTH,
                            default=enums.NAME_DEFAULT)
    description = models.TextField(
        default=enums.string_not_specify, max_length=enums.DESCRIPTION_MAX_LENGTH)
    avatar = models.TextField(default=enums.AVATAR_DEFAULT)
    cover = models.TextField(default='')
    followers = models.IntegerField(default=0)
    followings = models.IntegerField(default=0)


class Follow(models.Model):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followed')
