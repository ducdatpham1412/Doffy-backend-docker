from setting.models import Block
from rest_framework.serializers import ModelSerializer


class BlockSerializer(ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'
