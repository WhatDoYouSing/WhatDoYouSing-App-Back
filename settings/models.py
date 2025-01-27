from django.db import models

# Create your models here.

class Notice(models.Model):
    admin_emoji = models.IntegerField(default=0, verbose_name="운영자 프로필 이모지")
    admin_name = models.CharField(max_length=100, default="운영자", verbose_name="운영자 이름")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")
    title = models.CharField(max_length=255, verbose_name="공지 제목")
    content = models.TextField(verbose_name="공지 내용")

    class Meta:
        db_table = "notices"
        verbose_name = "공지"
        verbose_name_plural = "공지들"

    def __str__(self):
        return self.title
    
class FAQ(models.Model):
    title = models.CharField(max_length=255, verbose_name="FAQ 제목 (Q)")
    content = models.TextField(verbose_name="FAQ 내용 (A)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")

    class Meta:
        db_table = "faq"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ들"

    def __str__(self):
        return self.title