from setting import models
from setting.models import Information, Extend
from rest_framework import serializers


class InformationSerializer(serializers.ModelSerializer):
    facebook = serializers.CharField(
        required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Information
        exclude = ['user']
        read_only_fields = ['user']


class ChangeInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Information
        exclude = ['user']


class ExtendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extend
        exclude = ['user']
        read_only_fields = ['user']

    def to_representation(self, instance):
        res = {
            'theme': instance.theme,
            'language': instance.language,
            'display_avatar': instance.display_avatar,
            'bank_account': instance.user.bank_account,
            'bank_code': instance.user.bank_code,
        }
        return res


class ListBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Block
        exclude = ['block']
