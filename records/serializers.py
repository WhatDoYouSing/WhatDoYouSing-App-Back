from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from accounts.models import *
from notes.models import Notes, Plis
import random

# ✅ [레코드] 메인 Serializer
class MainRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = [
            'album_art'
        ]
    
# 📌 [레코드] 감정시집 Serializer
class EmotionsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = [
            
        ]

# 📌 [레코드] 단어모음집 Serializer
class WordsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = [
            
        ]