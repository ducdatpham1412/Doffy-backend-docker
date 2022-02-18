from django.db import models
from utilities import enums
from authentication.models import User
from datetime import datetime


class Information(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='information', primary_key=True, editable=False)
    gender = models.SmallIntegerField(default=enums.gender_female)
    birthday = models.DateTimeField(default=datetime(2000, 1, 1))


class Extend(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='setting_extend', primary_key=True, editable=False
    )
    theme = models.SmallIntegerField(default=enums.theme_light)
    language = models.SmallIntegerField(default=enums.language_vi)
    display_avatar = models.BooleanField(default=enums.display_avatar_no)


class Block(models.Model):
    block = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_block')
    blocked = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_blocked')
