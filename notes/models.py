from django.db import models
from accounts.models import User

# Create your models here.


class Emotions(models.Model):
    id = models.AutoField(primary_key=True)  # 감정 ID
    name = models.CharField(max_length=30)  # 감정 이름
    count = models.IntegerField(default=0)  # 각 태그 누적 개수

    def __str__(self):
        return self.name


class Times(models.Model):
    id = models.AutoField(primary_key=True)  # 시간 태그 ID
    name = models.CharField(max_length=50)  # 시간 태그 이름 (예: "새벽", "아침")
    count = models.IntegerField(default=0)  # 각 태그 누적 개수

    def __str__(self):
        return self.name


class Seasons(models.Model):
    id = models.AutoField(primary_key=True)  # 계절 태그 ID
    name = models.CharField(max_length=50)  # 계절 태그 이름 (예: "봄", "여름")
    count = models.IntegerField(default=0)  # 각 태그 누적 개수

    def __str__(self):
        return self.name


class Contexts(models.Model):
    id = models.AutoField(primary_key=True)  # 일상 맥락 태그 ID
    name = models.CharField(max_length=50)  # 일상 맥락 태그 이름 (예: "산책", "여행")
    count = models.IntegerField(default=0)  # 각 태그 누적 개수

    def __str__(self):
        return self.name


class Notes(models.Model):

    VISIBILITY_CHOICES = [
        ("public", "공개"),  # 전체 공개
        ("friends", "친구 공개"),  # 친구 공개
        ("private", "비공개"),  # 비공개
    ]

    id = models.AutoField(primary_key=True)  # 노트 고유 ID
    user = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.CASCADE
    )  # 게시물 작성자 ID
    created_at = models.DateTimeField(auto_now_add=True)  # 작성 날짜
    is_updated = models.BooleanField(default=False)  # 수정 여부
    album_art = models.CharField(
        max_length=200, null=True, blank=True
    )  # 앨범 아트(유튜브 썸네일 URL)
    song_title = models.CharField(max_length=200)  # 노래 제목(유튜브 영상 제목)
    artist = models.CharField(max_length=200)  # 아티스트 이름(유튜브 채널명)
    lyrics = models.TextField(null=True, blank=True)
    link = models.CharField(
        max_length=200, null=True, blank=True
    )  # 관련 링크(유튜브 URL 등)
    memo = models.TextField()  # 노트 내용(메모)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="public"
    )  # 공개 범위
    location_name = models.CharField(max_length=50, null=True, blank=True)  # 장소명
    location_address = models.TextField(null=True, blank=True)  # 장소명

    emotion = models.ForeignKey(
        Emotions,
        related_name="notes_emotion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )  # 감정
    tag_time = models.ManyToManyField(
        Times, related_name="tag_time", blank=True
    )  # 시간 태그
    tag_season = models.ManyToManyField(
        Seasons,
        related_name="tag_season",
        blank=True,
    )  # 계절 태그
    tag_context = models.ManyToManyField(
        Contexts,
        related_name="tag_context",
        blank=True,
    )  # 일상맥락 태그

    scrap_count = models.IntegerField(default=0)  # 스크랩 수
    # archive_count = models.IntegerField(default=0)  # 보관 수

    def __str__(self):
        return (
            f"{self.id}. {self.user.nickname} - {self.song_title} ({self.visibility})"
        )


# 노트에 다른 사용자가 감정 등록
class NoteEmotion(models.Model):
    note = models.ForeignKey(Notes, on_delete=models.CASCADE, verbose_name="노트")
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, verbose_name="사용자"
    )
    emotion = models.ForeignKey(Emotions, on_delete=models.CASCADE, verbose_name="감정")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="감정을 남긴 날짜"
    )

    class Meta:
        db_table = "note_emotions"
        verbose_name = "노트 감정"
        verbose_name_plural = "노트 감정들"

    def __str__(self):
        return f"{self.user.username} - {self.emotion.name} on {self.note.song_title}"


class Plis(models.Model):

    VISIBILITY_CHOICES = [
        ("public", "공개"),
        ("friends", "친구 공개"),
        ("private", "비공개"),
    ]

    id = models.AutoField(primary_key=True)  # 플리 고유 ID
    title = models.CharField(max_length=255, null=False)  # 플리 제목
    user = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.CASCADE
    )  # 게시물 작성자 ID
    is_updated = models.BooleanField(default=False)  # 수정 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 작성 날짜
    comments_count = models.IntegerField(default=0)  # 댓글 개수
    scrap_count = models.IntegerField(default=0)  # 스크랩 개수
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="public"
    )  # 공개 범위

    tag_time = models.ManyToManyField(
        Times,
        related_name="pli_tag_time",
        blank=True,
    )  # 시간 태그
    tag_season = models.ManyToManyField(
        Seasons,
        related_name="pli_tag_season",
        blank=True,
    )  # 계절 태그
    tag_context = models.ManyToManyField(
        Contexts,
        related_name="pli_tag_context",
        blank=True,
    )  # 일상맥락 태그

    def __str__(self):
        return self.title


class PliNotes(models.Model):

    id = models.AutoField(primary_key=True)  # 고유 ID
    plis = models.ForeignKey(
        Plis, related_name="plinotes", on_delete=models.CASCADE
    )  # 플리 ID (외래키)
    notes = models.ForeignKey(
        Notes, related_name="notes", on_delete=models.CASCADE
    )  # 노트 ID (외래키)
    note_memo = models.TextField(null=True, blank=True)  # 해당 노트에 대한 메모
    created_at = models.DateTimeField(auto_now_add=True)  # 추가 날짜


class NoteComment(models.Model):
    note = models.ForeignKey(
        Notes,
        on_delete=models.CASCADE,
        verbose_name="대상 노트",
        related_name="comments",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="댓글 작성자",
        related_name="note_comments",
    )
    content = models.TextField(verbose_name="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes = models.ManyToManyField(
        User, verbose_name="좋아요", related_name="liked_note_comments"
    )

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
        verbose_name="부모 댓글",
        related_name="replies",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="대댓글 작성자",
        related_name="note_replies",
    )
    mention = models.CharField(
        max_length=50, verbose_name="멘션 닉네임", default="", null=True, blank=True
    )
    content = models.TextField(verbose_name="대댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes = models.ManyToManyField(
        User, verbose_name="좋아요", related_name="liked_note_replies"
    )

    class Meta:
        db_table = "notes_replies"
        verbose_name = "노트 대댓글"
        verbose_name_plural = "노트 대댓글들"

    def __str__(self):
        return f"대댓글: {self.user.username} - {self.content[:20]}"


class PliComment(models.Model):
    pli = models.ForeignKey(
        Plis,
        on_delete=models.CASCADE,
        verbose_name="대상 플리",
        related_name="comments",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="댓글 작성자",
        related_name="pli_comments",
    )
    content = models.TextField(verbose_name="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes = models.ManyToManyField(
        User, verbose_name="좋아요", related_name="liked_pli_comments"
    )

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
        verbose_name="부모 댓글",
        related_name="replies",
    )
    user = models.ForeignKey(
        User,  # User 모델 참조
        on_delete=models.CASCADE,
        verbose_name="대댓글 작성자",
        related_name="pli_replies",
    )
    mention = models.CharField(
        max_length=50, verbose_name="멘션 닉네임", default="", null=True, blank=True
    )
    content = models.TextField(verbose_name="대댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    likes = models.ManyToManyField(
        User, verbose_name="좋아요", related_name="liked_pli_replies"
    )

    class Meta:
        db_table = "plis_replies"
        verbose_name = "플리 대댓글"
        verbose_name_plural = "플리 대댓글들"

    def __str__(self):
        return f"대댓글: {self.user.username} - {self.content[:20]}"


class CommentReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ("note comment", "note comment"),
        ("note reply", "note reply"),
        ("playlist comment", "playlist comment"),
        ("playlist reply", "playlist reply"),
    ]
    report_user = models.ForeignKey(
        User,
        verbose_name="신고 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_made",
    )
    issue_user = models.ForeignKey(
        User,
        verbose_name="위험 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_received",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(verbose_name="댓글/대댓글 내용")
    reason = models.TextField(verbose_name="신고 사유")
    type = models.CharField(
        max_length=20, choices=REPORT_TYPE_CHOICES, default="note comment"
    )
    content_id = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.report_user} -> {self.issue_user} ({self.type})"
