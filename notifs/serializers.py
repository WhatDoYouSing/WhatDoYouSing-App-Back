from rest_framework import serializers
from .models import Notification, Activity, Device
from notes.models import *
from accounts.models import User


class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]


class NotificationSerializer(serializers.ModelSerializer):
    actor_user = MiniUserSerializer(source="actor", read_only=True)
    notif_id = serializers.SerializerMethodField()
    target_content = serializers.SerializerMethodField()
    notif_emotion = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor_user",
            "notif_type",
            "notif_id",
            "content",
            "target_content",
            "notif_emotion",
            "is_read",
            "created_at",
        ]

    def get_notif_id(self, obj):
        # 요청 스키마가 char이므로 문자열로 변환
        return str(obj.obj_id) if obj.obj_id is not None else None

    # ----- 내부 헬퍼 -----
    def _get_target_instance(self, obj):
        # 뷰에서 주입한 target_map 우선 사용 → GFK N+1 방지
        target_map = self.context.get("target_map", {})
        if target_map:
            t = target_map.get((obj.ct_id, obj.obj_id))
            if t is not None:
                return t
        return getattr(obj, "target", None)  # GFK fallback

    def get_target_content(self, obj):
        t = self._get_target_instance(obj)
        if t is None:
            return None

        # --- NoteEmotion인 경우: 원글 노트의 memo를 보여주기 ---
        if isinstance(t, NoteEmotion):
            note = getattr(t, "note", None)
            if note:
                return (getattr(note, "memo", "") or "")[:200] or None

        # 기존 로직 (댓글/대댓글/노트/플리 처리)
        if isinstance(t, (NoteComment, PliComment, NoteReply, PliReply)):
            return (getattr(t, "content", "") or "")[:200] or None

        notif_type = (obj.notif_type or "").lower()
        if notif_type in {"emotion", "note_save", "pli_save"}:
            if isinstance(t, Notes):
                return (getattr(t, "memo", "") or "")[:200] or None
            # Plis 등 다른 모델 처리(있다면)...
        # fallback
        return (getattr(t, "content", "") or "")[:200] or None

    def get_notif_emotion(self, obj):
        if (obj.notif_type or "").lower() != "emotion":
            return None

        # 1) target이 NoteEmotion이면 바로 그 emotion.name 반환
        t = self._get_target_instance(obj)
        if isinstance(t, NoteEmotion):
            return getattr(getattr(t, "emotion", None), "name", None)

        # 2) target이 Notes인 경우 (혹시 signals가 Note로 저장한 경우) -> 조회
        actor_id = getattr(obj, "actor_id", None)
        note_id = obj.obj_id
        if actor_id and note_id:
            return (
                NoteEmotion.objects.filter(note_id=note_id, user_id=actor_id)
                .select_related("emotion")
                .order_by("-created_at")
                .values_list("emotion__name", flat=True)
                .first()
            )

        return None


# class ActivitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Activity
#         fields = ["id", "activity_type", "created_at"]
class ActivitySerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    parent_text = serializers.SerializerMethodField()
    target_text = serializers.SerializerMethodField()

    target_id = serializers.SerializerMethodField()
    # target_title = serializers.SerializerMethodField()
    target_owner_nickname = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "activity_type",
            "created_at",
            "text",
            "parent_text",
            "target_text",
            "target_type",
            "target_id",
            # "target_title",
            "target_owner_nickname",
        ]

    # ↓↓↓ helper ↓↓↓
    def _comment_snippet(self, obj, max_len=120):
        return (
            (obj.content[:max_len] + "…") if len(obj.content) > max_len else obj.content
        )

    def get_text(self, act):
        if act.activity_type in ["comment_note", "comment_pli"]:
            return self._comment_snippet(act.target)
        if act.activity_type in ["reply_note", "reply_pli"]:
            return self._comment_snippet(act.target)
        return None

    def get_parent_text(self, act):
        if act.activity_type in ["reply_note", "reply_pli"]:
            return self._comment_snippet(act.target.comment)
        return None

    def get_target_text(self, act):
        if act.activity_type in ["like_comment", "like_reply"]:
            return self._comment_snippet(act.target)
        return None

    def _get_target_instance(self, obj):
        # context에 미리 채운 매핑이 있으면 우선 사용 (뷰에서 넘겨주는 경우)
        target_map = self.context.get("target_map", {})
        if target_map:
            t = target_map.get((obj.ct_id, obj.obj_id))
            if t is not None:
                return t
        # fallback: GenericForeignKey (느리지만 안전)
        return getattr(obj, "target", None)

    def _resolve_to_original_post(self, target):
        """
        target이 comment/reply이면 원본(Plis or Notes) 객체를 반환.
        target이 이미 원본(Plis/Notes)이라면 그대로 반환.
        반환값: (original_obj_or_None, kind_str) where kind_str in ('pli', 'note', None)
        """
        if target is None:
            return None, None

        # 1) target이 Plis 또는 Notes (직접 대상)
        if isinstance(target, Plis) or hasattr(target, "title"):
            return target, "pli"
        if isinstance(target, Notes) or hasattr(target, "song_title"):
            return target, "note"

        # 2) target이 댓글 (PliComment / NoteComment)
        if isinstance(target, PliComment) or hasattr(target, "pli"):
            try:
                return target.pli, "pli"
            except Exception:
                return None, None
        if isinstance(target, NoteComment) or hasattr(target, "note"):
            try:
                return target.note, "note"
            except Exception:
                return None, None

        # 3) target이 대댓글 (PliReply / NoteReply)
        if (
            isinstance(target, PliReply)
            or hasattr(target, "comment")
            and hasattr(getattr(target, "comment", None), "pli")
        ):
            try:
                return target.comment.pli, "pli"
            except Exception:
                return None, None
        if (
            isinstance(target, NoteReply)
            or hasattr(target, "comment")
            and hasattr(getattr(target, "comment", None), "note")
        ):
            try:
                return target.comment.note, "note"
            except Exception:
                return None, None

        # fallback
        return None, None

    def get_target_id(self, obj):
        target = self._get_target_instance(obj)
        original, kind = self._resolve_to_original_post(target)
        return getattr(original, "id", None) if original else None

    """ def get_target_title(self, obj):
        target = self._get_target_instance(obj)
        original, kind = self._resolve_to_original_post(target)
        if not original:
            return None
        if kind == "pli":
            # Plis: use title
            return str(getattr(original, "title", None) or "")
        if kind == "note":
            # Notes: use song_title (프로젝트에 따라 다른 필드일 수 있음)
            return str(getattr(original, "song_title", None) or "")
        # fallback
        return str(original) """

    def get_target_owner_nickname(self, obj):
        target = self._get_target_instance(obj)
        original, kind = self._resolve_to_original_post(target)
        if not original:
            return None
        owner = getattr(original, "user", None)
        if not owner:
            return None
        return str(getattr(owner, "nickname", None) or getattr(owner, "username", None))

    def get_target_type(self, obj):
        NO_TARGET_TYPES = {"achievement", "emotion"}
        """
        'note' | 'pli' | None
        """
        if getattr(obj, "activity_type", None) in NO_TARGET_TYPES:
            return None
        target = self._get_target_instance(obj)
        original, kind = self._resolve_to_original_post(target)
        return kind  # already 'note' or 'pli' or None


class DeviceSerializer(serializers.ModelSerializer):
    expo_token = serializers.CharField(max_length=255)

    class Meta:
        model = Device
        fields = ["expo_token"]
