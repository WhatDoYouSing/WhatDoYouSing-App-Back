from rest_framework import serializers
from notes.models import *
from accounts.models import *
from accounts.serializers import UserSerializer

"""
# <노트> 탐색 결과 serializer
# Memo
class SearchNotesMemoSerializer(serializers.ModelSerializer):
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
            "emotion",
            "memo",
            "visibility",
            "created_at",
            "is_updated",
        ]


# Lyrics, Title, Singer
class SearchNotesLTSSerializer(serializers.ModelSerializer):
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
            "emotion",
            "visibility",
            "created_at",
            "is_updated",
        ]


# Location
class SearchNotesLocationSerializer(serializers.ModelSerializer):
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
            "emotion",
            "visibility",
            "created_at",
            "is_updated",
            "location_name",
            "location_address",
        ]
"""


# runserver 용. 테스트 후 tag 필드 없는 걸로
# Memo
class SearchNotesMemoSerializer(serializers.ModelSerializer):
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
            "emotion",
            "memo",
            "visibility",
            "created_at",
            "is_updated",
            "tag_time",
            "tag_season",
            "tag_context",
        ]


# Lyrics, Title, Singer
class SearchNotesLTSSerializer(serializers.ModelSerializer):
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
            "emotion",
            "visibility",
            "created_at",
            "is_updated",
            "tag_time",
            "tag_season",
            "tag_context",
        ]


# Location
class SearchNotesLocationSerializer(serializers.ModelSerializer):
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
            "emotion",
            "visibility",
            "created_at",
            "is_updated",
            "location_name",
            "location_address",
            "tag_time",
            "tag_season",
            "tag_context",
        ]


# 노트 탐색결과
class SearchNotesSerializer(serializers.ModelSerializer):
    Memo = SearchNotesMemoSerializer(many=True)  # 메모에서 검색된 노트
    Lyrics = SearchNotesLTSSerializer(many=True)  # 가사에서 검색된 노트
    Title = SearchNotesLTSSerializer(many=True)  # 곡명에서 검색된 노트
    Singer = SearchNotesLTSSerializer(many=True)  # 가수에서 검색된 노트
    Location = SearchNotesLocationSerializer(
        many=True
    )  # 위치에서 검색된 노트 (위치 정보 포함)


"""
# 노트 정보
class NotesSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    type = serializers.SerializerMethodField()  # 동적 필드 추가

    class Meta:
        model = Notes
        fields = [
            "type",
            "id",
            "user",
            "song_title",
            "artist",
            "album_art",
            "memo",
            "created_at",
        ]

    def get_type(self, obj):
        return "note"  # Notes는 "note"로 반환


# 플리 정보
class PlisSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    type = serializers.SerializerMethodField()  # 동적 필드 추가
    notes_count = serializers.SerializerMethodField()  # 포함된 노트 개수 추가

    class Meta:
        model = Plis
        fields = ["id", "title", "user", "created_at", "notes_count", "type"]

    def get_type(self, obj):
        return "pli"  # Plis는 "pli"로 반환

    def get_notes_count(self, obj):
        return obj.plis.count()  # 해당 플리에 포함된 노트 개수
"""
