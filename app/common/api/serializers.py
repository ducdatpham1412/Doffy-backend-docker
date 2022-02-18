from common.models import Images, Hobby, MyBubbles
from authentication.models import User
from rest_framework import serializers
from setting.api.serializers import InformationSerializer
from myprofile.api.serializers import ProfileSerializer
from setting.api.serializers import ExtendSerializer


class GetPassportSerializer(serializers.ModelSerializer):
    information = InformationSerializer()
    profile = ProfileSerializer()
    setting_extend = ExtendSerializer()

    class Meta:
        model = User
        fields = ['information', 'profile',
                  'setting_extend', 'facebook', 'email']

    def to_representation(self, instance):
        information = InformationSerializer(
            instance).to_representation(instance.information)
        profile = ProfileSerializer(
            instance).to_representation(instance.profile)
        setting = ExtendSerializer(instance).to_representation(
            instance.setting_extend)

        res = {
            'information': {
                'facebook': instance.facebook,
                'email': instance.email,
                'phone': instance.phone,
                **information
            },
            'profile': profile,
            'setting': setting
        }
        return res


class HobbySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hobby
        fields = '__all__'


class MyBubblesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyBubbles
        fields = '__all__'


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = '__all__'
