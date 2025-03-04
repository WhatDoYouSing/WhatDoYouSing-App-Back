from rest_framework import serializers
from notes.models import *
from accounts.models import *
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta

from rest_framework import serializers
from .models import Notes, Plis


class NotesSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # 동적 필드 추가

    class Meta:
        model = Notes
        fields = [
            "id",
            "song_title",
            "artist",
            "album_art",
            "memo",
            "created_at",
            "type",
        ]

    def get_type(self, obj):
        return "note"  # Notes는 "note"로 반환


class PlisSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # 동적 필드 추가
    notes_count = serializers.SerializerMethodField()  # 포함된 노트 개수 추가

    class Meta:
        model = Plis
        fields = ["id", "title", "user", "created_at", "notes_count", "type"]

    def get_type(self, obj):
        return "pli"  # Plis는 "pli"로 반환

    def get_notes_count(self, obj):
        return obj.plis.count()  # 해당 플리에 포함된 노트 개수
