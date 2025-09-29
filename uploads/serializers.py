import random
from rest_framework import serializers
from notes.models import *
from .models import *
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
        if "link" not in validated_data or validated_data.get("link") is None:
            validated_data["link"] = ""

        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])

        # context로 전달된 request에서 user 가져오기 (뷰에서 context={'request': request} 전달 필요)
        request_obj = self.context.get("request") if self.context else None
        user = getattr(request_obj, "user", None)

        note = Notes.objects.create(user=user, **validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note


# 노트 업로드(유튜브)
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

        request_obj = self.context.get("request") if self.context else None
        user = getattr(request_obj, "user", None)

        note = Notes.objects.create(user=user, **validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note


# 기본 앨범 커버 이미지 URL 리스트
DEFAULT_ALBUM_ART_IMAGES = [
    "https://ibb.co/Qv3qRk4n",
    "https://ibb.co/jP61YYqn",
    "https://ibb.co/nsYD3htM",
    "https://ibb.co/MxvhwqFP",
    "https://ibb.co/nsWN5XSY",
    "https://ibb.co/whwqjzLg",
    "https://ibb.co/xqJpQwCd",
    "https://ibb.co/k6XWfNwh",
    "https://ibb.co/j9x3F9M2",
    "https://ibb.co/h0f1c8z",
]


# 노트 업로드(직접)
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
        # 만약 album_art 필드에 값이 없거나 비어 있다면 기본 이미지를 할당
        if not validated_data.get("album_art"):
            validated_data["album_art"] = random.choice(DEFAULT_ALBUM_ART_IMAGES)
        # return super().create(validated_data)
        # link 방어 (song 업로드 같은 케이스에서 link가 없으면 빈 문자열)
        if "link" not in validated_data or validated_data.get("link") is None:
            validated_data["link"] = ""

        tag_time_data = validated_data.pop("tag_time", [])
        tag_season_data = validated_data.pop("tag_season", [])
        tag_context_data = validated_data.pop("tag_context", [])

        request_obj = self.context.get("request") if self.context else None
        user = getattr(request_obj, "user", None)

        note = Notes.objects.create(user=user, **validated_data)
        note.tag_time.set(tag_time_data)
        note.tag_season.set(tag_season_data)
        note.tag_context.set(tag_context_data)
        return note


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
    note_memo = serializers.CharField(
        required=False, allow_blank=True
    )  # 노트 메모 공란 가능하도록

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

        request_obj = self.context.get("request") if self.context else None
        user = getattr(request_obj, "user", None)

        plis = Plis.objects.create(user=user, **validated_data)
        plis.tag_time.set(tag_time_data)
        plis.tag_season.set(tag_season_data)
        plis.tag_context.set(tag_context_data)

        for plinote_item in plinotes_data:
            note = plinote_item["notes"]  # 선택된 노트 ID
            note_memo = plinote_item.get("note_memo", "")  # 없으면 빈 문자열

            PliNotes.objects.create(
                plis=plis,  # 플리와 연결
                notes=note,  # 노트 객체
                note_memo=note_memo,  # 해당 노트에 대한 메모
            )

        return plis

    def update(self, instance, validated_data):
        # 1) 중첩 plinotes 데이터 꺼내기
        plinotes_data = validated_data.pop("plinotes", None)

        # 2) 기본 필드 (title, visibility) 업데이트
        for attr in ("title", "visibility"):
            if attr in validated_data:
                setattr(instance, attr, validated_data.pop(attr))
        instance.save()

        # 3) M2M 태그들 업데이트
        if "tag_time" in validated_data:
            instance.tag_time.set(validated_data.pop("tag_time"))
        if "tag_season" in validated_data:
            instance.tag_season.set(validated_data.pop("tag_season"))
        if "tag_context" in validated_data:
            instance.tag_context.set(validated_data.pop("tag_context"))

        # 4) plinotes 중첩 처리
        if plinotes_data is not None:
            # (기존 관계 모두 날리고)
            instance.plinotes.all().delete()
            # (새로 받은 것들로 만들기)
            for item in plinotes_data:
                note = item["notes"]
                note_memo = item.get("note_memo", "")
                PliNotes.objects.create(
                    plis=instance,
                    notes=note,
                    note_memo=note_memo,
                )

        return instance


# 게시글 작성자 신고 시리얼라이저
class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = ["id", "issue_user", "reason", "created_at"]
        read_only_fields = ["id", "created_at", "issue_user"]

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("신고 사유를 입력해주세요.")
        return value

    # 추가 kwargs(report_user, issue_user)를 받아서 처리
    def create(self, validated_data, report_user=None, issue_user=None, **kwargs):
        # defensive copy
        data = validated_data.copy()

        # validated_data에 클라이언트가 보냈을 수 있는 충돌 키 제거
        data.pop("report_user", None)
        data.pop("user", None)  # 모델에서 user라고 쓸 경우 대비
        data.pop("issue_user", None)

        # report_user / issue_user를 kwargs 또는 context에서 보충
        if report_user is None:
            request = self.context.get("request")
            report_user = getattr(request, "user", None) if request else None

        if issue_user is None:
            issue_user = self.context.get("issue_user")

        if report_user is None or issue_user is None:
            raise serializers.ValidationError(
                "서버 내부 오류: 신고자 또는 대상 정보가 없습니다."
            )

        # 필요한 필드만 명시적으로 전달해도 안전 (예: reason)
        return UserReport.objects.create(
            report_user=report_user,
            issue_user=issue_user,
            **data,
        )


# 게시글 신고 시리얼라이저
class PostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        fields = ["id", "report_type", "content_id", "reason", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("신고 사유를 입력해주세요.")
        return value

    # save(report_user=..., issue_user=...) 를 받을 수 있게 처리
    def create(self, validated_data, report_user=None, issue_user=None, **kwargs):
        data = validated_data.copy()

        # 클라이언트가 보냈을지 모를 충돌 키 제거
        data.pop("report_user", None)
        data.pop("issue_user", None)
        data.pop("user", None)

        if report_user is None:
            request = self.context.get("request")
            report_user = getattr(request, "user", None) if request else None

        if issue_user is None:
            issue_user = self.context.get("issue_user")

        if report_user is None or issue_user is None:
            raise serializers.ValidationError(
                "서버 내부 오류: 신고자/대상 정보가 없습니다."
            )

        # 자기자신 신고 방지
        if report_user == issue_user:
            raise serializers.ValidationError("자신의 게시글은 신고할 수 없습니다.")

        return PostReport.objects.create(
            report_user=report_user,
            issue_user=issue_user,
            **data,
        )
