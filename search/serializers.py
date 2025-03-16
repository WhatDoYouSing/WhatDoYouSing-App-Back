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


# test 용. 테스트 후 tag 필드 없는 걸로
# 탐색결과(노트)
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


# test 용. 테스트 후 tag 필드 없는 걸로
# 탐색결과(플리)
# Memo
class SearchPlisMemoSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    note_count = serializers.SerializerMethodField()
    firstmemo = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()

    class Meta:
        model = Plis
        fields = [
            "id",
            "user",
            "note_count",
            "album_art",
            "title",
            "firstmemo",
            "visibility",
            "created_at",
            "is_updated",
            "tag_time",
            "tag_season",
            "tag_context",
        ]

    def get_note_count(self, obj):  # 인용된 노트 개수 카운트
        return PliNotes.objects.filter(plis=obj).count()

    def get_firstmemo(self, obj):  # 첫 번째 인용된 노트의 메모 반환
        first_note = PliNotes.objects.filter(plis=obj).order_by("created_at").first()
        return first_note.note_memo if first_note and first_note.note_memo else ""
        # 첫번째 노트에 대한 메모 없으면 빈문자열 반환

    def get_album_art(self, obj):
        """해당 플리에 포함된 노트의 앨범 아트 최대 4개 반환"""
        album_arts = PliNotes.objects.filter(plis=obj).values_list(
            "notes__album_art", flat=True
        )[:4]
        return list(album_arts) if album_arts else []


# Lyrics, SongTitle, Singer, PlisTitle
# 결과 정확도 확인 위해 잠시 relatednote 필드 추가 - 삭제하기
class SearchPlisLSSPSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    note_count = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()

    class Meta:
        model = Plis
        fields = [
            "id",
            "user",
            "note_count",
            "album_art",
            "title",
            "visibility",
            "created_at",
            "is_updated",
            "tag_time",
            "tag_season",
            "tag_context",
        ]

    def get_note_count(self, obj):
        return PliNotes.objects.filter(plis=obj).count()

    def get_album_art(self, obj):
        """해당 플리에 포함된 노트의 앨범 아트 최대 4개 반환"""
        album_arts = PliNotes.objects.filter(plis=obj).values_list(
            "notes__album_art", flat=True
        )[:4]
        return list(album_arts) if album_arts else []


# 플리 탐색결과
class SearchPlisSerializer(serializers.ModelSerializer):
    Memo = SearchPlisMemoSerializer(many=True)  # 메모에서 검색된 플리
    Lyrics = SearchPlisLSSPSerializer(many=True)  # 가사에서 검색된 플리
    SongTitle = SearchPlisLSSPSerializer(many=True)  # 곡명에서 검색된 플리
    Singer = SearchPlisLSSPSerializer(many=True)  # 가수에서 검색된 플리
    PlisTitle = SearchPlisLSSPSerializer(many=True)  # 플리 제목에서 검색된 플리


class SearchWritersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "username",
            "profile",
        ]
