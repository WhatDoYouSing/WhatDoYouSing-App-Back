# records/signals.py
from collections import Counter
from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db.models import F
from notes.models import Notes
from records.models import WordStat, NoteWord
from records.utils.noun_extractor import extract_nouns
from django.core.exceptions import ObjectDoesNotExist

from django.db.models import F

def _adjust_wordstat(user, year, month, counter, delta):
    """
    delta = +1 (증가) / -1 (감소)
    counter = Counter({'dream':2, 'story':1})
    """
    for noun, cnt in counter.items():
        try:
            # 트랜잭션 잠금으로 동시성 안전
            ws = (
                WordStat.objects
                .select_for_update()        # 현재 행 잠금
                .get(user=user, year=year, month=month, noun=noun)
            )
            new_val = ws.count + delta * cnt
            if new_val <= 0:
                ws.delete()                # 1) 0 이하면 삭제
            else:
                ws.count = new_val         # 2) 아니면 정상 업데이트
                ws.save(update_fields=["count"])
        except ObjectDoesNotExist:
            # 행이 없고 delta>0 일 때만 INSERT
            if delta > 0:
                WordStat.objects.create(
                    user=user,
                    year=year,
                    month=month,
                    noun=noun,
                    count=cnt,
                )


@receiver(post_save, sender=Notes)
def update_wordstat_on_save(sender, instance, created, **kwargs):
    if not instance.lyrics:
        return

    year, month = instance.created_at.year, instance.created_at.month
    user        = instance.user

    # 새 가사에서 명사 + 빈도
    new_counter = Counter(extract_nouns(instance.lyrics))

    with transaction.atomic():
        if not created:
            # ① 이전 가사의 빈도 차감
            old_lyrics  = sender.objects.get(pk=instance.pk).lyrics or ""
            old_counter = Counter(extract_nouns(old_lyrics))
            _adjust_wordstat(user, year, month, old_counter, delta=-1)
            NoteWord.objects.filter(note=instance).delete()

        # ② 새 가사 반영
        _adjust_wordstat(user, year, month, new_counter, delta=+1)

        # ③ NoteWord는 (note, noun) 1행만 저장
        NoteWord.objects.bulk_create(
            [NoteWord(note=instance, noun=n) for n in new_counter.keys()],
            ignore_conflicts=True,
        )

@receiver(pre_delete, sender=Notes)
def update_wordstat_on_delete(sender, instance, **kwargs):
    if not instance.lyrics:
        return
    year, month = instance.created_at.year, instance.created_at.month
    user        = instance.user
    counter     = Counter(extract_nouns(instance.lyrics))
    _adjust_wordstat(user, year, month, counter, delta=-1)