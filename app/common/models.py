from django.db import models
from authentication.models import User


def directory_path(instance, filename):
    return 'image/{0}'.format(filename)


class Images(models.Model):
    image = models.ImageField(upload_to='image/', blank=True, null=True)


class Hobby(models.Model):
    name = models.TextField()
    icon = models.TextField()


class MyBubbles(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='my_bubbles', editable=False)
    listHobbies = models.JSONField(encoder=None, default=dict)
    listDescriptions = models.JSONField(encoder=None, default=dict)
