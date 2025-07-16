from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from accounts.models import *
from notes.models import Notes, Plis
import random
from .models import *

# ✅ [레코드] 메인 Serializer
class MainRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = [
            'album_art'
        ]
    
# ✅ [레코드] 감정시집 Serializer
class EmotionsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = [
            'artist', 'song_title', 'lyrics'
        ]

# 📌 [레코드] 단어모음집 목록 Serializer
class WordStatSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WordStat
        fields = ("noun", "count")

# 📌 [레코드] 단어모음집 상세 Serializer
class NoteThumbSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notes
        fields = ("id", "lyrics")
