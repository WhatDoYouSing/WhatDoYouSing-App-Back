from django.db import models
from accounts.models import User


class ScrapList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="스크랩 유저")
    name = models.CharField(max_length=255, verbose_name="스크랩 리스트 이름")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 날짜")

    class Meta:
        db_table = "scrap_lists"
        verbose_name = "스크랩 리스트"
        verbose_name_plural = "스크랩 리스트들"

    def __str__(self):
        return f"{self.user.nickname} - {self.name}"


class ScrapNotes(models.Model):
    scrap_list = models.ForeignKey(
        ScrapList, on_delete=models.CASCADE, verbose_name="스크랩 리스트"
    )
    content_id = models.PositiveIntegerField(verbose_name="노트 ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="스크랩 날짜")

    class Meta:
        db_table = "scrap_notes"
        verbose_name = "스크랩 노트"
        verbose_name_plural = "스크랩 노트들"

    def __str__(self):
        return f"{self.scrap_list.name}에 스크랩된 노트: {self.content_object}"


class ScrapPlaylists(models.Model):
    scrap_list = models.ForeignKey(
        ScrapList, on_delete=models.CASCADE, verbose_name="스크랩 리스트"
    )
    content_id = models.PositiveIntegerField(verbose_name="플리 ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="스크랩 날짜")

    class Meta:
        db_table = "scrap_playlists"
        verbose_name = "스크랩 플리"
        verbose_name_plural = "스크랩 플리들"

    def __str__(self):
        # return f"{self.scrap_list.name}에 스크랩된 플리: {self.content_object}"
        return f"{self.scrap_list.name}에 스크랩된 플리: {self.content_id}"
