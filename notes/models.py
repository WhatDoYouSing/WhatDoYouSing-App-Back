from django.db import models

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
    link = models.CharField(max_length=200)  # 관련 링크(유튜브 URL 등)
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
        Times, related_name="tag_time", null=True, blank=True
    )  # 시간 태그
    tag_season = models.ManyToManyField(
        Seasons,
        related_name="tag_season",
        null=True,
        blank=True,
    )  # 계절 태그
    tag_context = models.ManyToManyField(
        Contexts,
        related_name="tag_context",
        null=True,
        blank=True,
    )  # 일상맥락 태그

    scrap_count = models.IntegerField(default=0)  # 스크랩 수
    archive_count = models.IntegerField(default=0)  # 보관 수

    def __str__(self):
        return self.song_title


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
    archive_count = models.IntegerField(default=0)  # 보관 개수
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="public"
    )  # 공개 범위

    tag_time = models.ManyToManyField(
        Times,
        related_name="pli_tag_time",
        null=True,
        blank=True,
    )  # 시간 태그
    tag_season = models.ManyToManyField(
        Seasons,
        related_name="pli_tag_season",
        null=True,
        blank=True,
    )  # 계절 태그
    tag_context = models.ManyToManyField(
        Contexts,
        related_name="pli_tag_context",
        null=True,
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
