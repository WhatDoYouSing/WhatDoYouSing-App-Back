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

from notifs.models import Notification, Activity, Device
from notifs.utils import send_expo_push


User = get_user_model()


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
        ct=ContentType.objects.get_for_model(obj),
        obj_id=obj.pk,
    )

    tokens = list(
        Device.objects.filter(user=target).values_list("expo_token", flat=True)
    )
    if tokens:
        send_expo_push(tokens, "새 알림", message, {"notif_id": notif.id})


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
def on_note_scrap(sender, instance, created, **kw):
    if not created:
        return
    saver = instance.scrap_list.user
    try:
        note_obj = Note.objects.get(pk=instance.content_id)
    except Note.DoesNotExist:
        return
    owner = note_obj.user
    if saver == owner:
        return
    _push_and_record(
        target=owner,
        actor=saver,
        notif_type="note_save",
        message=f"{saver.nickname} 님이 내 노트를 스크랩했습니다.",
        obj=instance,
    )
    # 스크랩은 활동 탭에 기록하지 않음.


@receiver(post_save, sender=ScrapPlaylists)
def on_pli_scrap(sender, instance, created, **kw):
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
    _push_and_record(
        target=owner,
        actor=saver,
        notif_type="pli_save",
        message=f"{saver.nickname} 님이 내 플리를 스크랩했습니다.",
        obj=instance,
    )


# ────────────────────────────────────────────────────────────────
# 3. 노트 감정
# ────────────────────────────────────────────────────────────────
NoteEmotion = apps.get_model("notes", "NoteEmotion")


@receiver(post_save, sender=NoteEmotion)
def on_emotion(sender, instance, created, **kw):
    if not created:
        return
    actor, owner = instance.user, instance.note.user
    if actor == owner:
        return
    _push_and_record(
        target=owner,
        actor=actor,
        notif_type="emotion",
        message=f"{actor.nickname} 님이 내 노트에 감정을 남겼습니다.",
        obj=instance,
    )
    _record_activity(user=actor, act_type="emotion", obj=instance)


# ────────────────────────────────────────────────────────────────
# 4. 댓글 / 대댓글
# ────────────────────────────────────────────────────────────────
NoteComment = apps.get_model("notes", "NoteComment")
NoteReply = apps.get_model("notes", "NoteReply")
PliComment = apps.get_model("notes", "PliComment")
PliReply = apps.get_model("notes", "PliReply")


@receiver(post_save, sender=NoteComment)
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

        liker = User.objects.get(pk=liker_id)

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
