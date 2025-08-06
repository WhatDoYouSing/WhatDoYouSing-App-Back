from rest_framework import serializers
from notes.models import *
from accounts.models import *
from social.models import UserFollows

# from accounts.serializers import UserSerializer

# 전부 다 tag 필드 삭제하기!


# account serializer에서 못가져오길래 걍 만듦.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]


# 탐색결과(전체)
# Writer 정보
class SearchAllWriterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]


# Note 타입 - 메모
class SearchAllMemoNotesSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="note")
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "type",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
        ]


# Pli 타입 - 메모
class SearchAllPlisSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="pli")
    user = UserSerializer(read_only=True)
    note_count = serializers.SerializerMethodField()
    firstmemo = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()

    class Meta:
        model = Plis
        fields = [
            "type",
            "id",
            "user",
            "note_count",
            "album_art",
            "title",
            "firstmemo",
            "visibility",
            "created_at",
            "is_updated",
            # "tag_time",
            # "tag_season",
            # "tag_context",
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


# Note 타입 - Lyrics, SongTitle, Singer
class SearchAllNotesLSSSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="note")
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "type",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
        ]


# Pli 타입 - SongTitle, Singer, PlisTitle
# 결과 정확도 확인 위해 잠시 relatednote 필드 추가 - 삭제하기
class SearchAllPlisSSPSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="pli")
    user = UserSerializer(read_only=True)
    note_count = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()

    class Meta:
        model = Plis
        fields = [
            "type",
            "id",
            "user",
            "note_count",
            "album_art",
            "title",
            "visibility",
            "created_at",
            "is_updated",
            # "tag_time",
            # "tag_season",
            # "tag_context",
        ]

    def get_note_count(self, obj):
        return PliNotes.objects.filter(plis=obj).count()

    def get_album_art(self, obj):
        """해당 플리에 포함된 노트의 앨범 아트 최대 4개 반환"""
        album_arts = PliNotes.objects.filter(plis=obj).values_list(
            "notes__album_art", flat=True
        )[:4]
        return list(album_arts) if album_arts else []


# Note 타입 - Location
class SearchAllNotesLocationSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="note")
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "type",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
        ]


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
            # "tag_time",
            # "tag_season",
            # "tag_context",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
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
            # "tag_time",
            # "tag_season",
            # "tag_context",
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


class FollowStatusSerializer(serializers.Serializer):
    is_following = serializers.BooleanField(read_only=True)
    is_follower = serializers.BooleanField(read_only=True)
    is_mutual_follow = serializers.SerializerMethodField()

    def get_is_mutual_follow(self, user):
        # annotate 된 값 사용
        return getattr(user, "is_following", False) and getattr(
            user, "is_follower", False
        )


class SearchWritersSerializer(serializers.ModelSerializer):
    follow_status = FollowStatusSerializer(source="*", read_only=True)

    class Meta:
        model = User
        fields = ["id", "nickname", "username", "profile", "follow_status"]
