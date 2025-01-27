from django.db import models
from notes.models import Note
from playlists.models import Pli
from accounts.models import User


class NoteComment(models.Model):
    note = models.ForeignKey(
        Note, 
        on_delete=models.CASCADE,
        verbose_name="대상 노트"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="댓글 작성자"
    )
    content = models.TextField(verbose_name="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes_count = models.IntegerField(default=0, verbose_name="좋아요 개수")
    replies_count = models.IntegerField(default=0, verbose_name="대댓글 개수")

    class Meta:
        db_table = "notes_comments"
        verbose_name = "노트 댓글"
        verbose_name_plural = "노트 댓글들"

    def __str__(self):
        return f"댓글: {self.user.username} - {self.content[:20]}"
    

class NoteReply(models.Model):
    comment = models.ForeignKey(
        NoteComment,  
        on_delete=models.CASCADE,
        verbose_name="부모 댓글"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="대댓글 작성자"
    )
    content = models.TextField(verbose_name="대댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes_count = models.IntegerField(default=0, verbose_name="좋아요 개수")

    class Meta:
        db_table = "notes_replies"
        verbose_name = "노트 대댓글"
        verbose_name_plural = "노트 대댓글들"

    def __str__(self):
        return f"대댓글: {self.user.username} - {self.content[:20]}"


class PliComment(models.Model):
    pli = models.ForeignKey(
        Pli,
        on_delete=models.CASCADE,
        verbose_name="대상 플리"
    )
    user = models.ForeignKey(
        User,  
        on_delete=models.CASCADE,
        verbose_name="댓글 작성자"
    )
    content = models.TextField(verbose_name="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes_count = models.IntegerField(default=0, verbose_name="좋아요 개수")
    replies_count = models.IntegerField(default=0, verbose_name="대댓글 개수")

    class Meta:
        db_table = "plis_comments"
        verbose_name = "플리 댓글"
        verbose_name_plural = "플리 댓글들"

    def __str__(self):
        return f"댓글: {self.user.username} - {self.content[:20]}"

class PliReply(models.Model):
    comment = models.ForeignKey(
        PliComment,
        on_delete=models.CASCADE,
        verbose_name="부모 댓글"
    )
    user = models.ForeignKey(
        User,  # User 모델 참조
        on_delete=models.CASCADE,
        verbose_name="대댓글 작성자"
    )
    content = models.TextField(verbose_name="대댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes_count = models.IntegerField(default=0, verbose_name="좋아요 개수")

    class Meta:
        db_table = "plis_replies"
        verbose_name = "플리 대댓글"
        verbose_name_plural = "플리 대댓글들"

    def __str__(self):
        return f"대댓글: {self.user.username} - {self.content[:20]}"
