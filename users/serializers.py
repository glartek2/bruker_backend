from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']
        # extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        Token.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
