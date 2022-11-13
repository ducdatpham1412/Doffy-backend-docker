from utilities.services import create_link_image
from rest_framework import serializers
from myprofile import models
from findme.mongo import mongoDb
from utilities.enums import account_shop, post_review


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    followings = serializers.SerializerMethodField()
    reputations = serializers.SerializerMethodField()
    account_type = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.user.id

    def get_account_type(self, obj):
        return obj.user.account_type

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
        if obj.user.account_type != account_shop:
            return 0

        list_post_review = mongoDb.discovery_post.find({
            'user_id': obj.user.id,
            'post_type': post_review,
        })
        list_post_review = list(list_post_review)

        if not len(list_post_review):
            return 0

        total_stars = 0
        for post in list_post_review:
            total_stars += post['stars']

        average_stars = total_stars / len(list_post_review)
        return average_stars

    def get_location(self, obj):
        return obj.location if obj.user.account_type == account_shop else ''

    class Meta:
        model = models.Profile
        fields = ['id', 'account_type', 'name', 'avatar', 'cover',
                  'description', 'followers', 'followings', 'reputations', 'location']
        read_only_fields = ['user']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Follow
        fields = '__all__'
