# from notes.models import Notes, Plis
# from moderation.models import NoteBlock, PliBlock, UserBlock


# def is_note_blocked(user, note: Notes) -> bool:
#     """로그인 사용자 기준 note 또는 note 작성자가 차단됐는지"""
#     if not user.is_authenticated:
#         return False
#     return (
#         NoteBlock.objects.filter(blocker=user, note=note).exists()
#         or UserBlock.objects.filter(blocker=user, blocked_user=note.user).exists()
#     )


# def is_pli_blocked(user, pli: Plis) -> bool:
#     """로그인 사용자 기준 pli 또는 작성자가 차단됐는지"""
#     if not user.is_authenticated:
#         return False
#     return (
#         PliBlock.objects.filter(blocker=user, pli=pli).exists()
#         or UserBlock.objects.filter(blocker=user, blocked_user=pli.user).exists()
#     )

from notes.models import Notes, Plis
from moderation.models import UserBlock, NoteBlock, PliBlock


def blocked_user_ids(user) -> set[int]:
    """작성자 차단 ID 집합"""
    if not user.is_authenticated:
        return set()
    return set(
        UserBlock.objects.filter(blocker=user).values_list("blocked_user_id", flat=True)
    )


def blocked_item_ids(user, model) -> set[int]:
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
    return set()


def is_note_blocked(user, note: Notes) -> bool:
    return note.id in blocked_item_ids(user, Notes) or note.user_id in blocked_user_ids(
        user
    )


def is_pli_blocked(user, pli: Plis) -> bool:
    return pli.id in blocked_item_ids(user, Plis) or pli.user_id in blocked_user_ids(
        user
    )
