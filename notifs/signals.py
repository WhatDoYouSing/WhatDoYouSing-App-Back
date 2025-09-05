# notifs/signals.py
"""
- 모든 도메인 이벤트 → Notification / Activity 레코드 생성
- Expo Push 발송까지 한 번에 처리

signals.py 가 앱 로딩 시 자동 등록되려면
notifs/apps.py -> NotifsConfig.ready() 에서 `from . import signals` 호출이 있어야 합니다.
"""
from django.apps import apps
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import re
import logging

from django.db import transaction
from django.db.models import Q

from notifs.models import Notification, Activity, Device
from notifs.utils import send_expo_push

logger = logging.getLogger(__name__)
User = get_user_model()

# 기존: try: UserBlock = apps.get_model("accounts", "UserBlock") ...
# 아래로 교체하세요.

# moderation 블록 모델들 가져오기 (있으면 사용, 없으면 None)
try:
    UserBlock = apps.get_model("moderation", "UserBlock")
    NoteBlock = apps.get_model("moderation", "NoteBlock")
    PliBlock = apps.get_model("moderation", "PliBlock")
    NoteCommentBlock = apps.get_model("moderation", "NoteCommentBlock")
    PliCommentBlock = apps.get_model("moderation", "PliCommentBlock")
    NoteReplyBlock = apps.get_model("moderation", "NoteReplyBlock")
    PliReplyBlock = apps.get_model("moderation", "PliReplyBlock")
except Exception:
    # 안전하게 None 처리 (테스트 환경 등)
    UserBlock = NoteBlock = PliBlock = None
    NoteCommentBlock = PliCommentBlock = NoteReplyBlock = PliReplyBlock = None


def _is_blocked_by(target_user, actor_user=None, obj=None):
    """
    target_user 가 알림의 수신자(=blocked 검사 기준)일 때,
    - actor_user 가 target_user 에 의해 차단되었는지(UserBlock)
    - 또는 target_user 가 특정 객체(노트/플리/댓글/대댓글)를 차단했는지(content-level block)

    인자:
      target_user: User instance (차단을 한 사람)
      actor_user:  User instance (행동 주체, optional)
      obj:         모델 인스턴스(Notes/Plis/NoteComment/NoteReply/... 등, optional)

    반환:
      True  -> 차단되어 알림/푸시를 보내지 말아야 함
      False -> 차단 아님
    """
    try:
        # 1) 유저 단위 차단: target_user 가 actor_user 를 차단했는지
        if UserBlock and actor_user is not None:
            if UserBlock.objects.filter(
                blocker=target_user, blocked_user=actor_user
            ).exists():
                return True

        # 2) 객체(콘텐츠) 단위 차단: target_user 가 특정 노트/플리/댓글/대댓글을 차단했는지
        if obj is not None:
            # 노트 차단
            if NoteBlock and obj.__class__.__name__ == "Notes":
                if NoteBlock.objects.filter(blocker=target_user, note=obj).exists():
                    return True

            # 플리 차단
            if PliBlock and obj.__class__.__name__ == "Plis":
                if PliBlock.objects.filter(blocker=target_user, pli=obj).exists():
                    return True

            # 노트 댓글 차단
            if NoteCommentBlock and obj.__class__.__name__ == "NoteComment":
                if NoteCommentBlock.objects.filter(
                    blocker=target_user, comment=obj
                ).exists():
                    return True

            # 플리 댓글 차단
            if PliCommentBlock and obj.__class__.__name__ == "PliComment":
                if PliCommentBlock.objects.filter(
                    blocker=target_user, comment=obj
                ).exists():
                    return True

            # 노트 대댓글 차단
            if NoteReplyBlock and obj.__class__.__name__ == "NoteReply":
                if NoteReplyBlock.objects.filter(
                    blocker=target_user, reply=obj
                ).exists():
                    return True

            # 플리 대댓글 차단
            if PliReplyBlock and obj.__class__.__name__ == "PliReply":
                if PliReplyBlock.objects.filter(
                    blocker=target_user, reply=obj
                ).exists():
                    return True

        return False
    except Exception:
        # 실패 시 안전하게 차단하지 않음(로그 남기는게 좋음)
        import logging

        logging.getLogger(__name__).exception("블록 검사 중 예외")
        return False


# helpers (signals.py 상단에 추가)
def _resolve_users_by_mention_string(mention_value):
    """
    mention_value 예시: "@alice, bob" 또는 "alice bob"
    반환: [User, ...] (중복 제거, 존재하는 사용자만)
    """
    if not mention_value:
        return []

    # split on commas or spaces; strip @ and whitespace
    parts = [
        p.strip().lstrip("@").strip()
        for p in re.split(r"[,\s]+", mention_value)
        if p.strip()
    ]
    if not parts:
        return []

    users = list(User.objects.filter(nickname__in=parts))
    # nickname may not be unique; this returns all matching users
    # preserve order & remove duplicates by id
    seen = set()
    result = []
    for u in users:
        if u.id not in seen:
            seen.add(u.id)
            result.append(u)
    return result


# ────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ────────────────────────────────────────────────────────────────
def _push_and_record(*, target, actor, notif_type, message, obj):
    """Notification 레코드 생성 + Expo Push 발송"""
    notif = Notification.objects.create(
        user=target,
        actor=actor,
        notif_type=notif_type,
        content=message,
        ct=ContentType.objects.get_for_model(obj) if obj is not None else None,
        obj_id=getattr(obj, "pk", None),
    )

    def _do_push():
        try:
            tokens = list(
                Device.objects.filter(user=target).values_list("expo_token", flat=True)
            )
            if tokens:
                send_expo_push(tokens, "새 알림", message, {"notif_id": notif.id})
        except Exception:
            logger.exception("send_expo_push 실패 for notif_id=%s", notif.id)

    transaction.on_commit(_do_push)
    return notif


def _record_activity(user, act_type, obj):
    Activity.objects.create(
        user=user,
        activity_type=act_type,
        ct=ContentType.objects.get_for_model(obj),
        obj_id=obj.pk,
    )


# ────────────────────────────────────────────────────────────────
# 1. 팔로우
# ────────────────────────────────────────────────────────────────
UserFollows = apps.get_model("social", "UserFollows")


@receiver(post_save, sender=UserFollows)
def on_follow(sender, instance, created, **kw):
    if not created:
        return
    follower, following = instance.follower, instance.following

    if _is_blocked_by(following, follower, obj=None):
        return

    _push_and_record(
        target=following,
        actor=follower,
        notif_type="follow",
        message=f"{follower.nickname} 님이 나를 팔로우했어요.",
        obj=instance,
    )
    # 활동 탭엔 팔로우를 별도로 기록하지 않기로 함.


# ────────────────────────────────────────────────────────────────
# 2. 노트/플리 스크랩
# ────────────────────────────────────────────────────────────────
ScrapNotes = apps.get_model("collects", "ScrapNotes")
ScrapPlaylists = apps.get_model("collects", "ScrapPlaylists")
Note = apps.get_model("notes", "Notes")
Pli = apps.get_model("notes", "Plis")


@receiver(post_save, sender=ScrapNotes)
def on_note_scrap(sender, instance, created, **kwargs):
    """if not created:
        return
    saver = instance.scrap_list.user
    try:
        note_obj = Note.objects.get(pk=instance.content_id)
    except Note.DoesNotExist:
        return
    owner = note_obj.user
    if saver == owner:
        return
    if _is_blocked_by(owner, saver, obj=note_obj):
        return

    _push_and_record(
        target=owner,
        actor=saver,
        notif_type="note_save",
        message=f"{saver.nickname} 님이 내 노트를 스크랩했습니다.",
        obj=note_obj,
    )
    # 스크랩은 활동 탭에 기록하지 않음."""
    if not created:
        return

    try:
        # 1) saver (스크랩한 사람)
        saver = None
        try:
            scrap_list = getattr(instance, "scrap_list", None)
            saver = (
                getattr(scrap_list, "user", None) if scrap_list is not None else None
            )
        except Exception as e:
            logger.exception(
                "on_note_scrap: failed to read scrap_list.user for ScrapNotes id=%s: %s",
                getattr(instance, "id", None),
                e,
            )
            saver = None

        if saver is None:
            logger.warning(
                "on_note_scrap: saver not found for ScrapNotes id=%s; skipping",
                getattr(instance, "id", None),
            )
            return

        # 2) note 객체: content_id 필드가 모델에서 정의되어 있으니 이걸 사용
        note_id = getattr(instance, "content_id", None)
        if not note_id:
            logger.warning(
                "on_note_scrap: no content_id on ScrapNotes id=%s; fields: %s",
                getattr(instance, "id", None),
                {
                    f.name: getattr(instance, f.name, None)
                    for f in instance._meta.fields
                },
            )
            return

        try:
            note_obj = Note.objects.get(pk=note_id)
        except Note.DoesNotExist:
            logger.warning(
                "on_note_scrap: Note does not exist for content_id=%s (ScrapNotes id=%s)",
                note_id,
                getattr(instance, "id", None),
            )
            return

        owner = getattr(note_obj, "user", None)
        if owner is None:
            logger.warning("on_note_scrap: note owner missing for note_id=%s", note_id)
            return

        # 3) 자기 스크랩이면 알림 안보냄
        if saver.id == owner.id:
            return

        # 4) 차단 검사 (유저/콘텐츠 단위)
        if _is_blocked_by(owner, saver, obj=note_obj):
            logger.debug(
                "on_note_scrap: blocked -> skipping notification (note_id=%s saver_id=%s owner_id=%s)",
                note_id,
                saver.id,
                owner.id,
            )
            return

        # 5) 알림 생성 (obj로 Notes 인스턴스 연결)
        display_name = (
            getattr(saver, "nickname", None)
            or getattr(saver, "username", None)
            or "사용자"
        )
        try:
            _push_and_record(
                target=owner,
                actor=saver,
                notif_type="note_save",
                message=f"{display_name} 님이 내 노트를 스크랩했습니다.",
                obj=note_obj,
            )
        except Exception:
            logger.exception(
                "on_note_scrap: failed to _push_and_record for note_id=%s saver_id=%s",
                note_id,
                saver.id,
            )

    except Exception:
        logger.exception(
            "on_note_scrap: unexpected error for ScrapNotes id=%s",
            getattr(instance, "id", None),
        )


@receiver(post_save, sender=ScrapPlaylists)
def on_pli_scrap(sender, instance, created, **kwargs):
    if not created:
        return
    saver = instance.scrap_list.user
    try:
        pli_obj = Pli.objects.get(pk=instance.content_id)
    except Pli.DoesNotExist:
        return
    owner = pli_obj.user
    if saver == owner:
        return

    if _is_blocked_by(owner, saver, obj=pli_obj):
        return

    _push_and_record(
        target=owner,
        actor=saver,
        notif_type="pli_save",
        message=f"{saver.nickname} 님이 내 플리를 스크랩했습니다.",
        obj=pli_obj,
    )


# ────────────────────────────────────────────────────────────────
# 3. 노트 감정
# ────────────────────────────────────────────────────────────────
NoteEmotion = apps.get_model("notes", "NoteEmotion")


@receiver(post_save, sender=NoteEmotion)
def on_emotion(sender, instance, created, **kwargs):
    if not created:
        return
    actor = instance.user
    note_obj = getattr(instance, "note", None)
    if note_obj is None:
        return
    owner = note_obj.user
    if actor == owner:
        return
    if _is_blocked_by(owner, actor, obj=note_obj):
        return

    _push_and_record(
        target=owner,
        actor=actor,
        notif_type="emotion",
        message=f"{actor.nickname} 님이 내 노트에 감정을 남겼습니다.",
        obj=note_obj,
    )
    _record_activity(user=actor, act_type="emotion", obj=instance)


# ────────────────────────────────────────────────────────────────
# 4. 댓글 / 대댓글
# ────────────────────────────────────────────────────────────────
NoteComment = apps.get_model("notes", "NoteComment")
NoteReply = apps.get_model("notes", "NoteReply")
PliComment = apps.get_model("notes", "PliComment")
PliReply = apps.get_model("notes", "PliReply")


""" @receiver(post_save, sender=NoteComment)
def on_note_comment(sender, instance, created, **kw):
    if not created:
        return
    actor, owner = instance.user, instance.note.user
    if actor != owner:
        _push_and_record(
            target=owner,
            actor=actor,
            notif_type="comment",
            message=f"{actor.nickname} 님이 내 노트에 댓글을 달았습니다.",
            obj=instance,
        )
    _record_activity(user=actor, act_type="comment_note", obj=instance)


@receiver(post_save, sender=PliComment)
def on_pli_comment(sender, instance, created, **kw):
    if not created:
        return
    actor, owner = instance.user, instance.pli.user
    if actor != owner:
        _push_and_record(
            target=owner,
            actor=actor,
            notif_type="comment",
            message=f"{actor.nickname} 님이 내 플리에 댓글을 달았습니다.",
            obj=instance,
        )
    _record_activity(user=actor, act_type="comment_pli", obj=instance)


@receiver(post_save, sender=NoteReply)
def on_note_reply(sender, instance, created, **kw):
    if not created:
        return
    actor, parent_owner = instance.user, instance.comment.user
    if actor != parent_owner:
        _push_and_record(
            target=parent_owner,
            actor=actor,
            notif_type="reply",
            message=f"{actor.nickname} 님이 내 댓글에 대댓글을 달았습니다.",
            obj=instance,
        )
    _record_activity(user=actor, act_type="reply_note", obj=instance)


@receiver(post_save, sender=PliReply)
def on_pli_reply(sender, instance, created, **kw):
    if not created:
        return
    actor, parent_owner = instance.user, instance.comment.user
    if actor != parent_owner:
        _push_and_record(
            target=parent_owner,
            actor=actor,
            notif_type="reply",
            message=f"{actor.nickname} 님이 내 댓글에 대댓글을 달았습니다.",
            obj=instance,
        )
    _record_activity(user=actor, act_type="reply_pli", obj=instance)
 """


@receiver(post_save, sender=NoteComment)
def on_note_comment(sender, instance, created, **kwargs):
    """
    노트 댓글: 원글 소유자에게 알림(작성자가 소유자 아닐 때).
    obj: 원글(Notes)로 저장해서 프론트가 노트로 이동하기 쉽도록 함.
    """
    if not created:
        return

    actor = instance.user
    note_obj = getattr(instance, "note", None)
    if note_obj is None:
        # 안전성: 대상 노트가 없으면 아무 작업도 하지 않음
        return

    owner = note_obj.user
    if owner and actor != owner:
        # 차단 또는 콘텐츠 블록 되어 있으면 알림 안보냄
        if not _is_blocked_by(owner, actor, obj=note_obj):
            _push_and_record(
                target=owner,
                actor=actor,
                notif_type="comment",
                message=f"{actor.nickname} 님이 내 노트에 댓글을 달았습니다.",
                # obj=instance,  # 원글(노트)을 obj로 연결 -> 프론트에서 원글로 이동하기 편함
                obj=note_obj,
            )

    # 활동 기록은 항상 남김 (사용자 행위 이력)
    _record_activity(user=actor, act_type="comment_note", obj=instance)


@receiver(post_save, sender=PliComment)
def on_pli_comment(sender, instance, created, **kwargs):
    """
    플리 댓글: 플리 소유자에게 알림(작성자가 소유자 아닐 때).
    obj: Plis
    """
    if not created:
        return

    actor = instance.user
    pli_obj = getattr(instance, "pli", None)
    if pli_obj is None:
        return

    owner = pli_obj.user
    if owner and actor != owner:
        if not _is_blocked_by(owner, actor, obj=pli_obj):
            _push_and_record(
                target=owner,
                actor=actor,
                notif_type="comment",
                message=f"{actor.nickname} 님이 내 플리에 댓글을 달았습니다.",
                # obj=instance,
                obj=pli_obj,
            )

    _record_activity(user=actor, act_type="comment_pli", obj=instance)


@receiver(post_save, sender=NoteReply)
def on_note_reply(sender, instance, created, **kwargs):
    """
    대댓글: 수신자 후보 = 부모 댓글 작성자, 원글 소유자, mention 대상들
    - 중복 제거
    - 각 수신자에 대해 차단/콘텐츠차단 검사 수행
    - obj는 수신자별로 적합한 원본(부모댓글/노트/대댓글)을 넘김
    """
    if not created:
        return

    actor = instance.user
    parent_comment = getattr(instance, "comment", None)  # NoteComment
    if parent_comment is None:
        return

    note_obj = getattr(parent_comment, "note", None)
    parent_author = getattr(parent_comment, "user", None)
    note_owner = getattr(note_obj, "user", None)

    recipients = {}  # user_obj -> set(reasons)

    # 부모 댓글 작성자
    if parent_author and parent_author.id != actor.id:
        recipients.setdefault(parent_author, set()).add("parent_comment")

    # 노트 소유자 (원글 소유자)
    if note_owner and note_owner.id not in (
        actor.id,
        getattr(parent_author, "id", None),
    ):
        recipients.setdefault(note_owner, set()).add("note_owner")

    # mention 처리 (닉네임 기반 - 정확도 주의)
    mention_str = getattr(instance, "mention", None)
    if mention_str:
        mentioned_users = _resolve_users_by_mention_string(mention_str)
        for mentioned in mentioned_users:
            if mentioned.id != actor.id:
                recipients.setdefault(mentioned, set()).add("mention")

    # 최종 수신자에게 알림 전송 (중복 제거)
    for user_obj, reasons in recipients.items():
        # 자기 자신에게는 알림 보내지 않음
        if user_obj.id == actor.id:
            continue

        # 콘텐츠 기반으로 obj 선택 (검사 및 serializer 용도)
        if "parent_comment" in reasons:
            check_obj = parent_comment

        elif "note_owner" in reasons:
            check_obj = note_obj

        elif "mention" in reasons:
            check_obj = instance

        else:
            check_obj = instance

        # 차단 검사: 수신자가 actor 또는 해당 콘텐츠를 차단했으면 건너뜀
        if _is_blocked_by(user_obj, actor, obj=check_obj):
            continue

        # 메시지 결정 (간단화: 'mention' 우선)
        if "mention" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "parent_comment" in reasons and "note_owner" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "parent_comment" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "note_owner" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        else:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."

        _push_and_record(
            target=user_obj,
            actor=actor,
            notif_type="reply",
            message=message,
            obj=instance,
        )

    # 활동 기록: actor 의 대댓글 활동 (원본은 대댓글 인스턴스)
    _record_activity(user=actor, act_type="reply_note", obj=instance)


@receiver(post_save, sender=PliReply)
def on_pli_reply(sender, instance, created, **kwargs):
    """
    플리 대댓글 처리 (NoteReply와 동일)
    """
    if not created:
        return

    actor = instance.user
    parent_comment = getattr(instance, "comment", None)  # PliComment
    if parent_comment is None:
        return

    pli_obj = getattr(parent_comment, "pli", None)
    parent_author = getattr(parent_comment, "user", None)
    pli_owner = getattr(pli_obj, "user", None)

    recipients = {}

    if parent_author and parent_author.id != actor.id:
        recipients.setdefault(parent_author, set()).add("parent_comment")

    if pli_owner and pli_owner.id not in (actor.id, getattr(parent_author, "id", None)):
        recipients.setdefault(pli_owner, set()).add("pli_owner")

    mention_str = getattr(instance, "mention", None)
    if mention_str:
        mentioned_users = _resolve_users_by_mention_string(mention_str)
        for mentioned in mentioned_users:
            if mentioned.id != actor.id:
                recipients.setdefault(mentioned, set()).add("mention")

    for user_obj, reasons in recipients.items():
        if user_obj.id == actor.id:
            continue

        if "parent_comment" in reasons:
            check_obj = parent_comment

        elif "pli_owner" in reasons:
            check_obj = pli_obj

        elif "mention" in reasons:
            check_obj = instance

        else:
            check_obj = instance

        if _is_blocked_by(user_obj, actor, obj=check_obj):
            continue

        if "mention" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "parent_comment" in reasons and "pli_owner" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "parent_comment" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        elif "pli_owner" in reasons:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."
        else:
            message = f"{actor.nickname} 님이 대댓글을 남겼어요."

        _push_and_record(
            target=user_obj,
            actor=actor,
            notif_type="reply",
            message=message,
            obj=instance,
        )

    _record_activity(user=actor, act_type="reply_pli", obj=instance)


# ────────────────────────────────────────────────────────────────
# 5. 댓글/대댓글 좋아요
# ────────────────────────────────────────────────────────────────
from django.contrib.auth import get_user_model

User = get_user_model()


def _handle_like(sender, instance, action, pk_set, **kwargs):
    """
    instance : Comment / Reply 객체
    pk_set   : { liker_id, ... }
    """
    if action != "post_add":
        return

    owner = instance.user  # 댓글/대댓글 작성자
    is_reply = hasattr(instance, "comment")  # Reply 는 comment 속성 보유
    like_type = "like_reply" if is_reply else "like_comment"

    for liker_id in pk_set:
        if liker_id == owner.id:
            continue  # 자기 글 좋아요면 알림 X

        try:
            liker = User.objects.get(pk=liker_id)
        except User.DoesNotExist:
            continue

        # 차단 검사: 수신자(owner)가 liker 를 차단했거나 해당 콘텐츠를 차단했으면 스킵
        if _is_blocked_by(owner, liker, obj=instance):
            continue

        _push_and_record(
            target=owner,
            actor=liker,
            notif_type="like",
            message=f"{liker.nickname} 님이 내 댓글/대댓글을 좋아했습니다.",
            obj=instance,
        )
        _record_activity(user=liker, act_type=like_type, obj=instance)


# NoteComment.likes
m2m_changed.connect(
    _handle_like,
    sender=NoteComment.likes.through,
    dispatch_uid="note_comment_like",
)

# NoteReply.likes
m2m_changed.connect(
    _handle_like,
    sender=NoteReply.likes.through,
    dispatch_uid="note_reply_like",
)

# PliComment.likes
m2m_changed.connect(
    _handle_like,
    sender=PliComment.likes.through,
    dispatch_uid="pli_comment_like",
)

# PliReply.likes
m2m_changed.connect(
    _handle_like,
    sender=PliReply.likes.through,
    dispatch_uid="pli_reply_like",
)


# ────────────────────────────────────────────────────────────────
# 6. 칭호 획득
# ────────────────────────────────────────────────────────────────
UserTitle = apps.get_model("accounts", "UserTitle")


@receiver(post_save, sender=UserTitle)
def on_title(sender, instance, created, **kw):
    if not created:
        return
    user = instance.user
    _record_activity(user=user, act_type="achievement", obj=instance)
