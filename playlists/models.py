from django.db import models
from accounts.models import User
from notes.models import Time, Season, Context, Note

class Pli(models.Model):
    user = models.ForeignKey(
        User,  # 사용자 모델을 가져옴 (User 모델)
        on_delete=models.CASCADE,
        verbose_name="플리 작성자"
    )
    title = models.CharField(max_length=255, verbose_name="플리 제목")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    is_updated = models.BooleanField(default=False, verbose_name="수정 여부")
    comments_count = models.IntegerField(default=0, verbose_name="댓글 개수")
    archive_count = models.IntegerField(default=0, verbose_name="보관 개수")
    visibility = models.CharField(
        max_length=50,
        choices=[('public', '공개'), ('friends', '친구만'), ('private', '비공개')],
        default='public',
        verbose_name="공개 범위"
    )
    
    tag_time = models.ForeignKey(
        Time, 
        on_delete=models.CASCADE,
        verbose_name="시간 태그"
    )
    tag_season = models.ForeignKey(
        Season, 
        on_delete=models.CASCADE,
        verbose_name="계절 태그"
    )
    tag_context = models.ForeignKey(
        Context, 
        on_delete=models.CASCADE,
        verbose_name="일상맥락 태그"
    )

    class Meta:
        db_table = "plis"
        verbose_name = "플리"
        verbose_name_plural = "플리들"

    def __str__(self):
        return self.title


class PliNote(models.Model):
    pli = models.ForeignKey(
        Pli, 
        on_delete=models.CASCADE,
        verbose_name="플리"
    )
    note = models.ForeignKey(
        Note,  
        on_delete=models.CASCADE,
        verbose_name="인용된 노트"
    )
    note_memo = models.TextField(verbose_name="해당 노트에 대한 메모")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="추가 날짜")

    class Meta:
        db_table = "pli_notes"
        verbose_name = "플리 노트"
        verbose_name_plural = "플리 노트들"

    def __str__(self):
        return f"플리: {self.pli.title}, 노트: {self.note.song_title}"