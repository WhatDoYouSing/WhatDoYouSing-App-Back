from notes.models import Notes, Plis, NoteComment, NoteReply, PliComment, PliReply
from moderation.models import (
    UserBlock,
    NoteBlock,
    PliBlock,
    NoteCommentBlock,
    NoteReplyBlock,
    PliCommentBlock,
    PliReplyBlock,
)
from typing import Set


def blocked_user_ids(user) -> Set[int]:
    """작성자 차단 ID 집합"""
    if not user.is_authenticated:
        return set()
    return set(
        UserBlock.objects.filter(blocker=user).values_list("blocked_user_id", flat=True)
    )


def blocked_item_ids(user, model) -> Set[int]:
    """노트 or 플리 차단 ID 집합"""
    if not user.is_authenticated:
        return set()

    if model is Notes:
        return set(
            NoteBlock.objects.filter(blocker=user).values_list("note_id", flat=True)
        )
    if model is Plis:
        return set(
            PliBlock.objects.filter(blocker=user).values_list("pli_id", flat=True)
        )

    if model is NoteComment:
        return set(
            NoteCommentBlock.objects.filter(blocker=user).values_list(
                "comment_id", flat=True
            )
        )
    if model is NoteReply:
        return set(
            NoteReplyBlock.objects.filter(blocker=user).values_list(
                "reply_id", flat=True
            )
        )
    if model is PliComment:
        return set(
            PliCommentBlock.objects.filter(blocker=user).values_list(
                "comment_id", flat=True
            )
        )
    if model is PliReply:
        return set(
            PliReplyBlock.objects.filter(blocker=user).values_list(
                "reply_id", flat=True
            )
        )

    return set()


def is_note_blocked(user, note: Notes) -> bool:
    return note.id in blocked_item_ids(user, Notes) or note.user_id in blocked_user_ids(
        user
    )


def is_pli_blocked(user, pli: Plis) -> bool:
    return pli.id in blocked_item_ids(user, Plis) or pli.user_id in blocked_user_ids(
        user
    )


def is_note_comment_blocked(user, comment: NoteComment) -> bool:
    return comment.id in blocked_item_ids(
        user, NoteComment
    ) or comment.user_id in blocked_user_ids(user)


def is_note_reply_blocked(user, reply: NoteReply) -> bool:
    return reply.id in blocked_item_ids(
        user, NoteReply
    ) or reply.user_id in blocked_user_ids(user)


def is_pli_comment_blocked(user, comment: PliComment) -> bool:
    return comment.id in blocked_item_ids(
        user, PliComment
    ) or comment.user_id in blocked_user_ids(user)


def is_pli_reply_blocked(user, reply: PliReply) -> bool:
    return reply.id in blocked_item_ids(
        user, PliReply
    ) or reply.user_id in blocked_user_ids(user)
