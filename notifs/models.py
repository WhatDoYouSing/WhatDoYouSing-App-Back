from django.db import models
from accounts.models  import User  # User 모델을 임포트합니다

class Notification(models.Model):
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
