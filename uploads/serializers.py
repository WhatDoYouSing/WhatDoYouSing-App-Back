import random
from rest_framework import serializers
from notes.models import *
from accounts.models import *
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta


# 노트 업로드(음원)
class Song_NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tag_time = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Times.objects.all(), required=False
    )
    tag_season = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Seasons.objects.all(), required=False
    )
    tag_context = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Contexts.objects.all(), required=False
    )

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

    def create(self, validated_data):
        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])
        note = Notes.objects.create(**validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note


# 노트 업로드(음원)
class YT_NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tag_time = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Times.objects.all(), required=False
    )
    tag_season = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Seasons.objects.all(), required=False
    )
    tag_context = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Contexts.objects.all(), required=False
    )

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

    def create(self, validated_data):
        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])
        note = Notes.objects.create(**validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note


# 기본 앨범 커버 이미지 URL 리스트
DEFAULT_ALBUM_ART_IMAGES = [
    "https://img.freepik.com/premium-vector/white-texture-round-striped-surface-white-soft-cover_547648-928.jpg",
    "https://images.unsplash.com/photo-1550684376-efcbd6e3f031?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8N3x8JUVBJUIyJTgwJUVDJTlEJTgwJUVDJTgzJTg5JTIwJUVCJUIwJUIwJUVBJUIyJUJEJUVEJTk5JTk0JUVCJUE5JUI0fGVufDB8fDB8fHww",
]


# 노트 업로드(음원)
class NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tag_time = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Times.objects.all(), required=False
    )
    tag_season = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Seasons.objects.all(), required=False
    )
    tag_context = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Contexts.objects.all(), required=False
    )

    def create(self, validated_data):
        # 만약 album_art 필드에 값이 없거나 비어 있다면 기본 이미지를 할당
        if not validated_data.get("album_art"):
            validated_data["album_art"] = random.choice(DEFAULT_ALBUM_ART_IMAGES)
        return super().create(validated_data)

    def create(self, validated_data):
        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])
        note = Notes.objects.create(**validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note

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


# My 노트 리스트
class NotesListSerializer(serializers.ModelSerializer):
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
            "emotion",
            "visibility",
            "created_at",
        ]


# 플리 업로드_notes
class PliNotesSerializer(serializers.ModelSerializer):
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
            "emotion",
            "memo",
        ]


# 플리 업로드_plinotes
class PliNoteUploadSerializer(serializers.ModelSerializer):
    # notes = PliNotesSerializer()
    notes = serializers.PrimaryKeyRelatedField(
        queryset=Notes.objects.all()
    )  # 노트 ID를 입력받아야 하므로 PrimaryKeyRelatedField로 설정
    selected_notes = PliNotesSerializer(source="notes", read_only=True)
    note_memo = serializers.CharField()

    class Meta:
        model = PliNotes
        fields = ["id", "notes", "selected_notes", "note_memo", "created_at"]


# 플리 업로드
class PliUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plinotes = PliNoteUploadSerializer(many=True, required=False, read_only=False)
    tag_time = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Times.objects.all(), required=False
    )
    tag_season = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Seasons.objects.all(), required=False
    )
    tag_context = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Contexts.objects.all(), required=False
    )

    class Meta:
        model = Plis
        fields = [
            "id",
            "title",
            "user",
            "plinotes",
            "visibility",
            "tag_time",
            "tag_season",
            "tag_context",
            "created_at",
        ]

        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])
        plinotes_data = validated_data.pop("plinotes", [])

        plis = Plis.objects.create(user=self.context["request"].user, **validated_data)
        plis.tag_time.set(tag_time_data)
        plis.tag_season.set(tag_season_data)
        plis.tag_context.set(tag_context_data)

        for plinote_item in plinotes_data:
            note = plinote_item["notes"]  # 선택된 노트 ID
            note_memo = plinote_item["note_memo"]  # 메모

            PliNotes.objects.create(
                plis=plis,  # 플리와 연결
                notes=note,  # 노트 객체
                note_memo=note_memo,  # 해당 노트에 대한 메모
            )

        return plis
