from django.db import models
from accounts.models import User

# Create your models here.

class UserFollows(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',
        verbose_name="팔로우를 시작한 유저"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_set',
        verbose_name="팔로우 당한 유저"
    )

    class Meta:
        db_table = "user_follows"                   # 테이블 이름
        verbose_name = "사용자 팔로우 관계"
        verbose_name_plural = "사용자 팔로우 관계"
        unique_together = ("follower", "following")  # 중복된 팔로우 방지

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
        