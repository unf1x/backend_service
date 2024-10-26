from rest_framework import serializers
from .models import Token


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['tx_hash', 'media_url', 'owner', 'unique_hash']
        extra_kwargs = {
            'tx_hash': {'required': False, 'allow_null': True},  # может быть пустым и может быть передано
            'media_url': {'required': True},
            'owner': {'required': True},
            'unique_hash': {'read_only': True}
        }
