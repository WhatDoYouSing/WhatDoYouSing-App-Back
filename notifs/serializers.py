from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Notification, Activity, Device
from notes.models import *
from accounts.models import User, Title


class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]


class NotificationSerializer(serializers.ModelSerializer):
    actor_user = MiniUserSerializer(source="actor", read_only=True)
    notif_id = serializers.SerializerMethodField()
    target_content = serializers.SerializerMethodField()
    notif_emotion = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

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

    def get_content(self, obj):
        actor = getattr(obj, "actor", None)
        name = (
            getattr(actor, "nickname", None)
            or getattr(actor, "username", None)
            or "사용자"
        )
        nt = (obj.notif_type or "").lower()
        if nt == "note_save":
            return f"{name} 님이 내 노트를 스크랩했습니다."
        if nt == "pli_save":
            return f"{name} 님이 내 플리를 스크랩했습니다."
        # 기타 타입 처리...
        return obj.content or ""

    def get_notif_id(self, obj):
        # 요청 스키마가 char이므로 문자열로 변환
        return str(obj.obj_id) if obj.obj_id is not None else None

    def _get_target_instance(self, obj):
        """
        1) 뷰에서 전달한 target_map 우선 사용 (context)
        2) GenericForeignKey fallback (obj.target)
        3) 마지막으로 ContentType을 이용해 직접 로드 (안전 장치)
        """
        # 1) context target_map
        target_map = self.context.get("target_map", {})
        if target_map:
            t = target_map.get((obj.ct_id, obj.obj_id))
            if t is not None:
                return t

        # 2) generic fk
        t = getattr(obj, "target", None)
        if t is not None:
            return t

        # 3) contenttype 직접 로드 (fallback)
        if obj.ct_id and obj.obj_id:
            try:
                ct = ContentType.objects.get_for_id(obj.ct_id)
                model = ct.model_class()
                if model:
                    return model.objects.filter(pk=obj.obj_id).first()
            except Exception:
                # 안전: 실패해도 None 반환
                return None
        return None

    def get_target_content(self, obj):
        """
        우선순위:
        1) NoteEmotion (obj가 NoteEmotion이면 -> 그 note.memo)
        2) 댓글/대댓글 인스턴스 -> .content
        3) Notes / Plis -> memo or title
        4) fallback: .content 속성이 있으면 사용
        """
        t = self._get_target_instance(obj)
        if not t:
            return None

        # 1) NoteEmotion 타입(또는 .note 속성이 있는 경우)
        #    -> 원글 노트의 memo 반환
        if hasattr(t, "note"):
            note = getattr(t, "note")
            if note:
                return (getattr(note, "memo", "") or "")[:200] or None

        # 2) 댓글/대댓글 인스턴스: content 반환
        if hasattr(t, "content"):
            content = getattr(t, "content", None)
            if content:
                return content[:200]

        # 3) Notes / Plis 직접 대상
        if isinstance(t, Notes):
            return (getattr(t, "memo", "") or "")[:200] or None
        if isinstance(t, Plis):
            # Plis는 title이 대표 텍스트, memo가 있다면 우선
            memo = getattr(t, "memo", None)
            if memo:
                return memo[:200]
            title = getattr(t, "title", None)
            return (title or "")[:200] or None

        # 4) 마지막 폴백: content 속성 있으면 사용, 없으면 None
        return (getattr(t, "content", "") or "")[:200] or None

    def get_notif_emotion(self, obj):
        if (obj.notif_type or "").lower() != "emotion":
            return None

        # 1) target이 NoteEmotion이면 바로 그 emotion.name 반환
        t = self._get_target_instance(obj)
        """ if isinstance(t, NoteEmotion):
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

        return None """
        # target이 NoteEmotion이면 바로 emotion.name 반환
        if t is not None and hasattr(t, "emotion"):
            return getattr(getattr(t, "emotion", None), "name", None)

        # fallback: DB에서 찾기 (가장 최근)
        note_id = obj.obj_id
        actor_id = getattr(obj, "actor_id", None)
        if not note_id or not actor_id:
            return None

        try:
            ne = (
                NoteEmotion.objects.filter(note_id=note_id, user_id=actor_id)
                .select_related("emotion")
                .order_by("-created_at")
                .first()
            )
            if ne:
                return getattr(getattr(ne, "emotion", None), "name", None)
        except Exception:
            return None

        return None


class MiniTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ("id", "name", "emoji")


class ActivitySerializer(serializers.ModelSerializer):
    target_user = serializers.SerializerMethodField()
    activity_id = serializers.SerializerMethodField()
    parent_type = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    activity_content = serializers.SerializerMethodField()
    activity_emotion = serializers.SerializerMethodField()
    activity_achievement = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "target_user",
            "activity_type",
            "activity_id",
            "parent_type",
            "content",
            "activity_content",
            "activity_emotion",
            "activity_achievement",
            "is_read",
            "created_at",
        ]

    # ---------------- helpers ----------------
    # target_map 우선으로 target 인스턴스 얻기 (뷰에서 context로 채워줌)
    def _get_target_instance(self, obj):
        target_map = self.context.get("target_map", {})
        if target_map:
            t = target_map.get((obj.ct_id, obj.obj_id))
            if t is not None:
                return t
        # GenericFK fallback
        t = getattr(obj, "target", None)
        if t is not None:
            return t
        # 마지막 수단: ContentType으로 직접 로드
        if getattr(obj, "ct_id", None) and getattr(obj, "obj_id", None):
            try:
                ct = ContentType.objects.get_for_id(obj.ct_id)
                model = ct.model_class()
                if model:
                    return model.objects.filter(pk=obj.obj_id).first()
            except Exception:
                return None
        return None

    # ---------------- target_user ----------------
    def get_target_user(self, obj):
        """
        활동의 '대상' 유저 규칙:
        - comment_note  : NoteComment -> note.user
        - comment_pli   : PliComment  -> pli.user
        - reply_note    : NoteReply   -> (우선 parent comment.user) 없으면 note.user
        - reply_pli     : PliReply    -> (우선 parent comment.user) 없으면 pli.user
        - like_comment  : NoteComment -> comment.user
        - like_reply    : NoteReply   -> reply.user
        - emotion       : NoteEmotion -> note.user
        - achievement   : 대상 없음 -> None
        """
        t = self._get_target_instance(obj)
        if not t:
            return None

        a = (obj.activity_type or "").lower()
        owner = None

        if a == "comment_note":
            owner = getattr(getattr(t, "note", None), "user", None)

        elif a == "comment_pli":
            owner = getattr(getattr(t, "pli", None), "user", None)

        elif a == "reply_note":
            owner = getattr(getattr(t, "comment", None), "user", None) or getattr(
                getattr(getattr(t, "comment", None), "note", None), "user", None
            )

        elif a == "reply_pli":
            owner = getattr(getattr(t, "comment", None), "user", None) or getattr(
                getattr(getattr(t, "comment", None), "pli", None), "user", None
            )

        elif a == "like_comment":
            # 좋아요 대상 = 댓글 작성자
            owner = getattr(t, "user", None)

        elif a == "like_reply":
            # 좋아요 대상 = 대댓글 작성자
            owner = getattr(t, "user", None) or getattr(
                getattr(t, "comment", None), "user", None
            )

        elif a == "emotion":
            owner = getattr(getattr(t, "note", None), "user", None)

        elif a == "achievement":
            owner = None

        # 혹시라도 못찾았을 때, 마지막 보루 (actor와 같으면 None 유지)
        if owner is None:
            maybe = getattr(t, "user", None)
            if maybe and maybe.id != obj.user_id:
                owner = maybe

        return MiniUserSerializer(owner).data if owner else None

    # ---------------- parent_type ----------------
    def get_parent_type(self, obj):
        """
        상위 컨테이너가 노트인지 플리인지 반환: "note" | "pli" | None
        - comment_*/reply_*: t.note or t.pli 또는 t.comment.note/pli를 따라 올라감
        - like_comment/like_reply: 대상 댓글/대댓글에서 부모를 따라 올라감
        - emotion: t.note → "note"
        - 그 외: t가 직접 원글(Notes/Plis)이면 그에 맞게 판단
        """
        a = (obj.activity_type or "").lower()
        if a == "achievement":
            return None  # ← 명시적으로 null
        t = self._get_target_instance(obj)
        if not t:
            return None

        # 1) 직접 원글일 수 있음 (Notes/Plis)
        if hasattr(t, "song_title") or t.__class__.__name__ == "Notes":
            return "note"
        if hasattr(t, "title") or t.__class__.__name__ == "Plis":
            return "pli"

        # 2) NoteEmotion: note가 부모
        if hasattr(t, "note") and getattr(t, "note", None) is not None:
            return "note"

        # 3) Comment: note/pli 중 하나를 부모로 가짐
        if hasattr(t, "pli") and getattr(t, "pli", None) is not None:
            return "pli"

        # 4) Reply: comment를 통해 note/pli로 올라감
        c = getattr(t, "comment", None)
        if c is not None:
            if hasattr(c, "note") and getattr(c, "note", None) is not None:
                return "note"
            if hasattr(c, "pli") and getattr(c, "pli", None) is not None:
                return "pli"

        return None

    # ---------------- 이하 기존 필드들 (activity_id, content, activity_content, activity_emotion, activity_achievement) ----------------
    def get_activity_id(self, obj):
        """
        라우팅용 id:
          - emotion              -> 해당 '노트'의 id
          - comment_* / reply_*  -> 해당 '댓글/대댓글'의 id
          - like_comment         -> 좋아요한 '댓글'의 id
          - like_reply           -> 좋아요한 '대댓글'의 id
          - 기타                  -> target(또는 obj_id) 그대로
        """
        t = self._get_target_instance(obj)
        if t is None:
            # fallback: 저장된 obj_id 그대로 반환
            return obj.obj_id

        a = (obj.activity_type or "").lower()

        # 1) 감정: NoteEmotion 인스턴스 -> note.id
        if a == "emotion":
            note = getattr(t, "note", None)
            return getattr(note, "id", None)

        # 2) 댓글/대댓글: 실제 대상의 pk
        if a in ("comment_note", "comment_pli", "reply_note", "reply_pli"):
            return getattr(t, "id", None)

        # 3) 좋아요: 좋아요의 대상(Comment/Reply)의 pk
        if a in ("like_comment", "like_reply"):
            return getattr(t, "id", None)

        # 4) 기타(칭호 등): 대상 객체 pk(없으면 obj_id)
        return getattr(t, "id", None) or obj.obj_id

    def get_content(self, obj):
        mapping = {
            "like_comment": "댓글 좋아요",
            "like_reply": "대댓글 좋아요",
            "comment_note": "노트에 댓글을 남겼습니다.",
            "comment_pli": "플리에 댓글을 남겼습니다.",
            "reply_note": "노트에 대댓글을 남겼습니다.",
            "reply_pli": "플리에 대댓글을 남겼습니다.",
            "emotion": "노트에 감정을 남겼습니다.",
            "achievement": "칭호를 획득했습니다.",
        }
        return mapping.get(
            (obj.activity_type or "").lower(), str(obj.activity_type or "")
        )

    def _snippet(self, text, max_len=200):
        if not text:
            return None
        text = str(text)
        return text if len(text) <= max_len else text[:max_len] + "…"

    def get_activity_content(self, obj):
        """
        활동 타입별로 콘텐츠 스니펫을 반환:
          - comment_*, reply_*      : 내가 쓴 댓글/대댓글 내용
          - like_comment, like_reply: 내가 좋아요한 댓글/대댓글 내용
          - emotion                 : 원글 노트의 메모
          - 그 외(백업)             : Notes.memo / Plis.title / content
        """
        t = self._get_target_instance(obj)
        if not t:
            return None

        a = (obj.activity_type or "").lower()

        # 1) 내가 쓴 댓글/대댓글
        if a in ("comment_note", "comment_pli", "reply_note", "reply_pli"):
            return self._snippet(getattr(t, "content", "") or "")

        # 2) 내가 좋아요를 누른 댓글/대댓글
        if a in ("like_comment", "like_reply"):
            return self._snippet(getattr(t, "content", "") or "")

        # 3) 감정: 원글 노트 메모
        if a == "emotion":
            note = getattr(t, "note", None)
            if note:
                return self._snippet(getattr(note, "memo", "") or "")

        # 4) 백업 경로들
        if isinstance(t, Notes):
            return self._snippet(getattr(t, "memo", "") or "")
        if isinstance(t, Plis):
            memo = getattr(t, "memo", None)
            if memo:
                return self._snippet(memo)
            return self._snippet(getattr(t, "title", "") or "")

        # 마지막 백업: content 속성이 있으면 사용
        content = getattr(t, "content", None)
        if content:
            return self._snippet(content)

        return None

    def get_activity_emotion(self, obj):
        if (obj.activity_type or "").lower() != "emotion":
            return None
        target = self._get_target_instance(obj)
        if target is not None and hasattr(target, "emotion"):
            return getattr(getattr(target, "emotion", None), "name", None)
        # fallback: search NoteEmotion if needed (omitted here for brevity)
        return None

    def get_activity_achievement(self, obj):
        if (obj.activity_type or "").lower() != "achievement":
            return None
        target = self._get_target_instance(obj)
        title = None
        if target is None:
            return None
        title = getattr(target, "title", None) or getattr(target, "titles", None)
        if title is None and isinstance(target, Title):
            title = target
        if title is None:
            tid = getattr(target, "title_id", None) or getattr(target, "id", None)
            if tid:
                title = Title.objects.filter(pk=tid).first()
        if not title:
            return None
        return MiniTitleSerializer(title).data


class DeviceSerializer(serializers.ModelSerializer):
    expo_token = serializers.CharField(max_length=255)

    class Meta:
        model = Device
        fields = ["expo_token"]
