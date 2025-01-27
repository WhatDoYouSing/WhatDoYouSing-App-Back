from django.db import models
from accounts.models import User

# 태그
class Time(models.Model):
    name = models.CharField(max_length=100, verbose_name="시간 태그 이름")  # 예: "새벽", "아침"
    count = models.IntegerField(default=0, verbose_name="누적 개수")

    class Meta:
        db_table = "times"
        verbose_name = "시간 태그"
        verbose_name_plural = "시간 태그들"

    def __str__(self):
        return self.name


class Season(models.Model):
    name = models.CharField(max_length=100, verbose_name="계절 태그 이름")  # 예: "봄", "여름"
    count = models.IntegerField(default=0, verbose_name="누적 개수")

    class Meta:
        db_table = "seasons"
        verbose_name = "계절 태그"
        verbose_name_plural = "계절 태그들"

    def __str__(self):
        return self.name


class Context(models.Model):
    name = models.CharField(max_length=100, verbose_name="일상맥락 태그 이름")  # 예: "산책", "여행"
    count = models.IntegerField(default=0, verbose_name="누적 개수")

    class Meta:
        db_table = "contexts"
        verbose_name = "일상맥락 태그"
        verbose_name_plural = "일상맥락 태그들"

    def __str__(self):
        return self.name
    
class Emotion(models.Model):
    name = models.CharField(max_length=10, verbose_name="감정 이름") 
    count = models.IntegerField(default=0, verbose_name="누적 개수")

    class Meta:
        db_table = "emotions"
        verbose_name = "감정"
        verbose_name_plural = "감정들"

    def __str__(self):
        return self.name

class Note(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="작성자"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    is_updated = models.BooleanField(default=False, verbose_name="수정 여부")
    album_art = models.TextField(blank=True, null=True, verbose_name="앨범 아트")
    song_title = models.CharField(max_length=255, verbose_name="노래 제목")
    artist = models.CharField(max_length=255, verbose_name="아티스트 이름")
    lyrics = models.TextField(blank=True, null=True, verbose_name="가사")
    link = models.TextField(blank=True, null=True, verbose_name="관련 링크")
    memo = models.TextField(blank=True, null=True, verbose_name="노트 내용")
    visibility = models.CharField(
        max_length=50, 
        choices=[('public', '공개'), ('friends', '친구만'), ('private', '비공개')],
        default='public', 
        verbose_name="공개 범위"
    )
    location_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="장소명")
    location_address = models.TextField(blank=True, null=True, verbose_name="장소 주소")
    emotion = models.ForeignKey(
        'Emotion',  # Emotion 모델 참조
        on_delete=models.CASCADE,
        verbose_name="감정"
    )

    tag_times = models.ManyToManyField('Time', blank=True, verbose_name="시간 태그")
    tag_seasons = models.ManyToManyField('Season', blank=True, verbose_name="계절 태그")
    tag_contexts = models.ManyToManyField('Context', blank=True, verbose_name="일상맥락 태그")
    
    scrap_count = models.IntegerField(default=0, verbose_name="스크랩 수")
    archive_count = models.IntegerField(default=0, verbose_name="보관 수")

    class Meta:
        db_table = "notes"
        verbose_name = "노트"
        verbose_name_plural = "노트들"

    def __str__(self):
        return f"{self.user.nickname}: {self.song_title} - {self.artist}"

# 노트에 다른 사용자가 감정 등록
class NoteEmotion(models.Model):
    note = models.ForeignKey(
        Note, 
        on_delete=models.CASCADE,
        verbose_name="노트"
    )
    user = models.ForeignKey(
        User,  
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    emotion = models.ForeignKey(
        Emotion,  
        on_delete=models.CASCADE,
        verbose_name="감정"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="감정을 남긴 날짜")

    class Meta:
        db_table = "note_emotions"
        verbose_name = "노트 감정"
        verbose_name_plural = "노트 감정들"

    def __str__(self):
        return f"{self.user.username} - {self.emotion.name} on {self.note.song_title}"
