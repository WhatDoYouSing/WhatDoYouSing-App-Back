# collects/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from moderation.models import UserBlock, NoteBlock, PliBlock
from collects.models import ScrapList, ScrapNotes, ScrapPlaylists
from notes.models import Notes, Plis

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=UserBlock)
def remove_user_scraps(sender, instance, created, **kwargs):
    if not created:
        return
    blocker = instance.blocker
    blocked_user = instance.blocked_user

    # 내 보관함들
    scrap_lists = ScrapList.objects.filter(user=blocker)
    # 차단된 사용자가 쓴 노트/플리 ID
    note_ids = Notes.objects.filter(user=blocked_user).values_list("id", flat=True)
    pli_ids = Plis.objects.filter(user=blocked_user).values_list("id", flat=True)

    # 보관함에서 삭제
    ScrapNotes.objects.filter(
        scrap_list__in=scrap_lists, content_id__in=note_ids
    ).delete()
    ScrapPlaylists.objects.filter(
        scrap_list__in=scrap_lists, content_id__in=pli_ids
    ).delete()


@receiver(post_save, sender=NoteBlock)
def remove_note_scraps(sender, instance, created, **kwargs):
    if not created:
        return
    blocker = instance.blocker
    note = instance.note

    scrap_lists = ScrapList.objects.filter(user=blocker)
    ScrapNotes.objects.filter(scrap_list__in=scrap_lists, content_id=note.id).delete()


@receiver(post_save, sender=PliBlock)
def remove_pli_scraps(sender, instance, created, **kwargs):
    if not created:
        return
    blocker = instance.blocker
    pli = instance.pli

    scrap_lists = ScrapList.objects.filter(user=blocker)
    ScrapPlaylists.objects.filter(
        scrap_list__in=scrap_lists, content_id=pli.id
    ).delete()
