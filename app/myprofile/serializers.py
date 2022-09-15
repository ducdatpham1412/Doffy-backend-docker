from utilities.services import create_link_image
from rest_framework import serializers
from myprofile import models
from findme.mongo import mongoDb
from utilities.enums import total_reputation


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    followings = serializers.SerializerMethodField()
    reputations = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.user.id

    def get_avatar(self, obj):
        return create_link_image(obj.avatar)

    def get_cover(self, obj):
        return create_link_image(obj.cover)

    def get_followers(self, obj):
        count = models.Follow.objects.filter(followed=obj.user.id).count()
        return count

    def get_followings(self, obj):
        count = models.Follow.objects.filter(follower=obj.user.id).count()
        return count

    def get_reputations(self, obj):
        total = mongoDb.total_items.find_one({
            'type': total_reputation,
            'user_id': obj.user.id,
        })
        if not total:
            return 0
        return total['value']

    class Meta:
        model = models.Profile
        fields = ['id', 'name', 'avatar', 'cover',
                  'description', 'followers', 'followings', 'reputations']
        read_only_fields = ['user']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Follow
        fields = '__all__'
