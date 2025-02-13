from django.db import models

class Notice(models.Model):
    title = models.CharField(max_length=255, verbose_name="공지 제목")
    manager_profile = models.IntegerField(default=0)
    manager_name = models.CharField(default='운영자', max_length=30)
    content = models.TextField(verbose_name="공지 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")

    class Meta:
        db_table = "notices"
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="질문")
    answer = models.TextField(verbose_name="답변")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성 날짜")

    class Meta:
        db_table = "faqs"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def __str__(self):
        return self.question
