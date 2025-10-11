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
    parent_type = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor_user",
            "notif_type",
            "notif_id",
            "parent_type",
            "parent_id",
            "content",
            "target_content",
            "notif_emotion",
            "is_read",
            "created_at",
        ]

    # NotificationSerializer 클래스 내부에 추가
    def _normalized_notif_type(self, obj):
        nt = (obj.notif_type or "").lower()
        if nt != "like":
            return nt

        # obj.notif_type == "like" 인 경우: target 인스턴스로 판별
        t = self._get_target_instance(obj)
        # reply 인스턴스는 보통 부모 comment 참조(.comment) 를 가짐 -> like_reply
        try:
            if t is not None:
                # reply 객체인지(부모 comment 속성 존재 & comment가 비어있지 않음)
                if hasattr(t, "comment") and getattr(t, "comment", None) is not None:
                    return "like_reply"
                # reply는 아니면 기본적으로 comment 좋아요로 간주
                return "like_comment"
        except Exception:
            pass

        # 마지막 보루: ContentType 기반 추론
        try:
            if getattr(obj, "ct_id", None):
                model_name = ContentType.objects.get_for_id(obj.ct_id).model
                if model_name and "reply" in model_name:
                    return "like_reply"
        except Exception:
            pass

        return "like_comment"

    def get_content(self, obj):
        # actor에서 표시할 이름 추출 (닉네임 우선, 없으면 username, 없으면 "사용자")
        actor = getattr(obj, "actor", None)
        actor_name = (
            getattr(actor, "nickname", None)
            or getattr(actor, "username", None)
            or "사용자"
        )
        nt = self._normalized_notif_type(obj)

        # 명시된 템플릿 매핑
        if nt == "follow":
            return f"{actor_name}님이 나를 팔로우했어요."
        if nt == "note_save":
            return f"{actor_name}님이 내 노트를 저장했어요."
        if nt == "pli_save":
            return f"{actor_name}님이 내 플리를 저장했어요."
        if nt == "emotion":
            return f"{actor_name}님이 내 노트에 감정을 남겼어요."
        if nt == "comment":
            return f"{actor_name}님이 댓글을 남겼어요."
        if nt == "reply":
            return f"{actor_name}님이 대댓글을 남겼어요."

        # 좋아요 처리: 기존 DB가 'like'만 사용하는 경우와, 'like_reply' 같이 분리한 경우 모두 대응
        if nt == "like_comment":
            # 기본(기존) : 댓글에 좋아요로 보여주기
            return f"{actor_name}님이 댓글에 좋아요를 남겼어요."
        if nt in ("like_reply", "like (미정)"):
            # 명시적으로 대댓글 좋아요 타입이 들어온 경우
            return f"{actor_name}님이 대댓글에 좋아요를 남겼어요."

        # fallback: 기존 content 필드를 그대로 사용하거나 빈 문자열 반환
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

    def _resolve_parent_post_from_target(self, target):
        """
        target 인스턴스에서 원글(Notes/Plis)의 타입과 id를 찾아 반환.
        반환: (parent_type, parent_id) where parent_type in ('note', 'pli') or (None, None)
        """
        if target is None:
            return None, None

        # 1) target 자체가 Notes / Plis
        if Notes is not None and isinstance(target, Notes):
            return "note", getattr(target, "id", None)
        if Plis is not None and isinstance(target, Plis):
            return "pli", getattr(target, "id", None)

        # 2) NoteEmotion -> target.note
        if hasattr(target, "note"):
            note = getattr(target, "note", None)
            if note:
                return "note", getattr(note, "id", None)

        # 3) NoteComment -> .note, PliComment -> .pli
        # 4) NoteReply -> .comment.note, PliReply -> .comment.pli
        # 5) 일반 댓글/대댓글(타입 판별용): .comment 속성 유무로 reply인지 판단 가능
        # NoteComment / NoteReply
        if NoteComment is not None and isinstance(target, NoteComment):
            note = getattr(target, "note", None)
            if note:
                return "note", getattr(note, "id", None)
        if NoteReply is not None and isinstance(target, NoteReply):
            parent_comment = getattr(target, "comment", None)
            if parent_comment:
                note = getattr(parent_comment, "note", None)
                if note:
                    return "note", getattr(note, "id", None)

        # PliComment / PliReply
        if PliComment is not None and isinstance(target, PliComment):
            pli = getattr(target, "pli", None)
            if pli:
                return "pli", getattr(pli, "id", None)
        if PliReply is not None and isinstance(target, PliReply):
            parent_comment = getattr(target, "comment", None)
            if parent_comment:
                pli = getattr(parent_comment, "pli", None)
                if pli:
                    return "pli", getattr(pli, "id", None)

        # 6) 일반 속성 기반 fallback
        if hasattr(target, "note"):
            n = getattr(target, "note", None)
            if n:
                return "note", getattr(n, "id", None)
        if hasattr(target, "pli"):
            p = getattr(target, "pli", None)
            if p:
                return "pli", getattr(p, "id", None)

        # 마지막으로 target에 user와 연결된 parent가 없다면 None
        return None, None

    def get_parent_type(self, obj):
        t = self._get_target_instance(obj)
        pt, _ = self._resolve_parent_post_from_target(t)
        return pt

    def get_parent_id(self, obj):
        t = self._get_target_instance(obj)
        _, pid = self._resolve_parent_post_from_target(t)
        return pid


class MiniTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ("id", "name", "emoji")


class ActivitySerializer(serializers.ModelSerializer):
    target_user = serializers.SerializerMethodField()
    activity_id = serializers.SerializerMethodField()
    parent_type = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
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
            "parent_id",
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

    def _resolve_root(self, t):
        """
        주어진 대상 t (comment/reply/NoteEmotion/Notes/Plis 등)에서
        루트 컨테이너를 찾아 반환 (root_type, root_id)
        root_type: "note" | "pli" | None
        """
        if t is None:
            return None, None

        # 1) t가 직접 원글인 경우
        # Notes: has song_title or class name
        if isinstance(t, Notes) or hasattr(t, "song_title"):
            return "note", getattr(t, "id", None)
        # Plis: has title or class name
        if isinstance(t, Plis) or hasattr(t, "title"):
            return "pli", getattr(t, "id", None)

        # 2) NoteEmotion: .note
        if hasattr(t, "note") and getattr(t, "note", None) is not None:
            n = getattr(t, "note", None)
            return "note", getattr(n, "id", None)

        # 3) 댓글/댓글류: .note or .pli
        if hasattr(t, "note") and getattr(t, "note", None) is not None:
            return "note", getattr(getattr(t, "note"), "id", None)
        if hasattr(t, "pli") and getattr(t, "pli", None) is not None:
            return "pli", getattr(getattr(t, "pli"), "id", None)

        # 4) reply(대댓글)인 경우: .comment 를 통해 부모 comment로 올라감
        c = getattr(t, "comment", None)
        if c is not None:
            # comment가 NoteComment인지 PliComment인지 확인
            if hasattr(c, "note") and getattr(c, "note", None) is not None:
                return "note", getattr(getattr(c, "note"), "id", None)
            if hasattr(c, "pli") and getattr(c, "pli", None) is not None:
                return "pli", getattr(getattr(c, "pli"), "id", None)

        # 마지막 보루: comment가 직접 note/pli로 연결되어 있지 않다면 None
        return None, None

    # ---------------- parent_type / parent_id ----------------
    def get_parent_type(self, obj):
        # achievement 은 항상 None
        a = (obj.activity_type or "").lower()
        if a == "achievement":
            return None

        t = self._get_target_instance(obj)
        root_type, _ = self._resolve_root(t)
        return root_type

    def get_parent_id(self, obj):
        a = (obj.activity_type or "").lower()
        if a == "achievement":
            return None

        t = self._get_target_instance(obj)
        _, root_id = self._resolve_root(t)
        return root_id

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
        """
        activity_type 기반 메시지 템플릿
        - comment_note / comment_pli : {target_nickname}님에게 댓글을 남겼어요.
        - reply_note   / reply_pli   : {target_nickname}님에게 대댓글을 남겼어요.
        - like_comment : {target_nickname}님의 댓글에 좋아요를 남겼어요.
        - like_reply   : {target_nickname}님의 대댓글에 좋아요를 남겼어요.
        - emotion      : {target_nickname}님의 노트에 감정을 남겼어요.
        - achievement  : 〈{achievement_name}〉 칭호와 프로필을 획득했어요.
        """
        a = (obj.activity_type or "").lower()

        # target nickname 얻기 (get_target_user가 MiniUserSerializer 데이터 반환)
        target_user_data = self.get_target_user(obj)
        target_nickname = None
        if isinstance(target_user_data, dict):
            # MiniUserSerializer이름 필드를 실제로 무엇으로 쓰는지(예: nickname/username) 따라 조정
            target_nickname = target_user_data.get("nickname") or target_user_data.get(
                "username"
            )
        if not target_nickname:
            target_nickname = "사용자"

        # achievement 는 title 이름을 가져와서 별도 템플릿 적용
        if a == "achievement":
            title_info = self.get_activity_achievement(obj)
            title_name = None
            if isinstance(title_info, dict):
                title_name = title_info.get("name")
            if title_name:
                return f"〈{title_name}〉 칭호와 프로필을 획득했어요."
            # fallback
            return "칭호를 획득했습니다."

        if a in ("comment_note", "comment_pli"):
            return f"{target_nickname}님에게 댓글을 남겼어요."

        if a in ("reply_note", "reply_pli"):
            return f"{target_nickname}님에게 대댓글을 남겼어요."

        if a == "like_comment":
            return f"{target_nickname}님의 댓글에 좋아요를 남겼어요."

        if a == "like_reply":
            return f"{target_nickname}님의 대댓글에 좋아요를 남겼어요."

        if a == "emotion":
            return f"{target_nickname}님의 노트에 감정을 남겼어요."

        # 기존 기본 메시지 포맷이 필요하면 여기서 처리 (보존용)
        default_map = {
            "like_comment": "댓글 좋아요",
            "like_reply": "대댓글 좋아요",
            "comment_note": "노트에 댓글을 남겼습니다.",
            "comment_pli": "플리에 댓글을 남겼습니다.",
            "reply_note": "노트에 대댓글을 남겼습니다.",
            "reply_pli": "플리에 대댓글을 남겼습니다.",
            "emotion": "노트에 감정을 남겼습니다.",
            "achievement": "칭호를 획득했습니다.",
        }
        return default_map.get(a, str(obj.activity_type or ""))

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
