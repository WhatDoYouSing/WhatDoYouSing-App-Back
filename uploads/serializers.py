import random
from rest_framework import serializers
from notes.models import *
from accounts.models import *
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta


# 노트 업로드(음원)
class Song_NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "id",
            "user",
            "album_art",
            "song_title",
            "artist",
            "lyrics",
            "location_name",
            "location_address",
            "emotion",
            "memo",
            "visibility",
            "tag_time",
            "tag_season",
            "tag_context",
            "created_at",
        ]


# 노트 업로드(음원)
class YT_NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "id",
            "user",
            "link",
            "album_art",
            "song_title",
            "artist",
            "lyrics",
            "location_name",
            "location_address",
            "emotion",
            "memo",
            "visibility",
            "tag_time",
            "tag_season",
            "tag_context",
            "created_at",
        ]


# 기본 앨범 커버 이미지 URL 리스트
DEFAULT_ALBUM_ART_IMAGES = [
    "https://img.freepik.com/premium-vector/white-texture-round-striped-surface-white-soft-cover_547648-928.jpg",
    "https://images.unsplash.com/photo-1550684376-efcbd6e3f031?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8N3x8JUVBJUIyJTgwJUVDJTlEJTgwJUVDJTgzJTg5JTIwJUVCJUIwJUIwJUVBJUIyJUJEJUVEJTk5JTk0JUVCJUE5JUI0fGVufDB8fDB8fHww",
]


# 노트 업로드(음원)
class NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    def create(self, validated_data):
        # 만약 album_art 필드에 값이 없거나 비어 있다면 기본 이미지를 할당
        if not validated_data.get("album_art"):
            validated_data["album_art"] = random.choice(DEFAULT_ALBUM_ART_IMAGES)
        return super().create(validated_data)

    class Meta:
        model = Notes
        fields = [
            "id",
            "user",
            "album_art",
            "song_title",
            "artist",
            "lyrics",
            "location_name",
            "location_address",
            "emotion",
            "memo",
            "visibility",
            "tag_time",
            "tag_season",
            "tag_context",
            "created_at",
        ]
