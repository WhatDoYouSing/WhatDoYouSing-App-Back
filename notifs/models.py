from django.db import models
from accounts.models import User  # User 모델을 임포트합니다

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


""" class Notification(models.Model):
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='알림을 받은 사용자')
    keyword = models.CharField(max_length=255, verbose_name='알림 키워드')
    content = models.TextField(verbose_name='알림 내용')
    is_read = models.BooleanField(default=False, verbose_name='읽음 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='알림 생성 날짜')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='읽은 날짜')
    contents_type = models.CharField(max_length=50, verbose_name='원본 게시물 유형')
    contents_id = models.IntegerField(verbose_name='원본 게시물 ID')
    contents = models.TextField(verbose_name='원본 게시물 내용')

    class Meta:
        db_table = 'notifications'  
        verbose_name = '알림'
        verbose_name_plural = '알림들'

    def __str__(self):
        return f'Notification for {self.user.username} - {self.keyword}'
 """


class Device(models.Model):
    """Expo Push Token 저장 (iOS 전용이지만 Android도 그대로 사용 가능)"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expo_token = models.CharField("Expo Push Token", max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id}:{self.expo_token[:10]}…"


class Notification(models.Model):
    """타인이 ‘나’에게 남긴 상호작용 (알림 탭)"""

    TYPE = [
        ("follow", "팔로우"),
        ("note_save", "내 노트 저장"),
        ("pli_save", "내 플리 저장"),
        ("emotion", "내 노트 감정"),
        ("comment", "댓글"),
        ("reply", "대댓글"),
        ("like", "댓글 좋아요"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="actions_sent",
        null=True,  # ← 추가
        blank=True,  # ← 추가
        verbose_name="행동 주체",
    )
    notif_type = models.CharField(
        max_length=20,
        choices=TYPE,
        null=True,  # 임시
        blank=True,
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # 원본 객체(선택)
    ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    obj_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey("ct", "obj_id")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_notif_type_display()}] {self.actor} → {self.user}"


class Activity(models.Model):
    """내가 남긴 상호작용 + 칭호 획득 (활동 탭)"""

    TYPE = [
        ("like_comment", "댓글 좋아요"),
        ("like_reply", "대댓글 좋아요"),
        ("comment_note", "노트 댓글"),
        ("comment_pli", "플리 댓글"),
        ("reply_note", "노트 대댓글"),
        ("reply_pli", "플리 대댓글"),
        ("emotion", "감정 남김"),
        ("achievement", "칭호 획득"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=20, choices=TYPE)
    ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    obj_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey("ct", "obj_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.get_activity_type_display()}"
