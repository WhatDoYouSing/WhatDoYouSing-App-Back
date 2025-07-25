# notes/utils/blocking.py
from notes.models import NoteBlock, PliBlock, UserBlock, Notes, Plis


def is_note_blocked(user, note: Notes) -> bool:
    """user 기준으로 note 또는 note 작성자가 차단됐는지"""
    if not user.is_authenticated:
        return False
    return (
        NoteBlock.objects.filter(user=user, note=note).exists()
        or UserBlock.objects.filter(user=user, blocked_user=note.user).exists()
    )


def is_pli_blocked(user, pli: Plis) -> bool:
    """user 기준으로 pli 또는 작성자가 차단됐는지"""
    if not user.is_authenticated:
        return False
    return (
        PliBlock.objects.filter(user=user, pli=pli).exists()
        or UserBlock.objects.filter(user=user, blocked_user=pli.user).exists()
    )
