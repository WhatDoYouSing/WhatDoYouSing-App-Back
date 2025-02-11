from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import *

class SignUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id','username','password','email','nickname','required_consent','push_notification_consent','marketing_consent']

    def create(self, validated_data):
        user = User(
            username = validated_data['username'],
            password = validated_data['password'],
            email = validated_data['email'],
            nickname = validated_data['nickname'],
            required_consent = validated_data['required_consent'],
            push_notification_consent = validated_data['push_notification_consent'],
            marketing_consent = validated_data['marketing_consent']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user
    
User = get_user_model()

class LogInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email is None:
            raise serializers.ValidationError('이메일을 입력해주세요.')
        if password is None:
            raise serializers.ValidationError('비밀번호를 입력해주세요.')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 사용자입니다.')

        if not user.check_password(password):
            raise serializers.ValidationError('잘못된 비밀번호입니다.')

        # RefreshToken 생성
        token = RefreshToken.for_user(user)
        
        data = {
            'id': user.id,
            'email': user.email,
            'nickname': user.nickname,
            'profile': user.profile,
            'access_token': str(token.access_token),
            'refresh_token': str(token),
        }

        return data
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]