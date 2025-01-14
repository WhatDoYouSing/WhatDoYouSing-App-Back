from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="이메일 주소")
    username = models.CharField(max_length=150, unique=True, verbose_name="아이디")
    notif_token = models.TextField(null=True, blank=True, verbose_name="FCM 토큰")
    password_hash = models.CharField(max_length=128, verbose_name="암호화된 비밀번호")
    nickname = models.CharField(max_length=50, verbose_name="닉네임")
    profile = models.IntegerField(null=True, blank=True, verbose_name="프로필")  # titles 테이블과 연결 가능
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name="칭호")
    # 소셜 로그인 제공자 선택 (애플, 카카오, 구글)
    auth_provider = models.CharField(
        max_length=50,
        choices=[
            ("apple", "Apple"),
            ("kakao", "Kakao"),
            ("google", "Google"),
        ],
        verbose_name="소셜 로그인 제공자",
    )
    auth_provider_id = models.CharField(max_length=255, verbose_name="소셜 로그인 사용자 ID")
    auth_provider_email = models.EmailField(
        unique=True, null=True, blank=True, verbose_name="소셜 로그인 이메일"
    )
    required_consent_date = models.DateTimeField(null=True, blank=True, verbose_name="필수 동의 날짜")
    push_notification_consent = models.BooleanField(default=False, verbose_name="푸시알림 동의 여부")
    marketing_consent = models.BooleanField(default=False, verbose_name="마케팅 정보 수신 동의 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="계정 생성 날짜")
    last_use_at = models.DateTimeField(default=now, verbose_name="마지막 접속 날짜")
    
    class Meta:
        db_table = "users"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"
    
    def __str__(self):
        return self.username
    
class UserDeletion(models.Model):
    REASON_CHOICES = [
        (1, "다른 사용자들의 콘텐츠가 부족해서"),
        (2, "올리고 싶은 콘텐츠가 적어서"),
        (3, "기능 사용 방법이 편리하지 않아서"),
        (4, "원하는 기능이 없어서"),
        (5, "호기심에 설치한 앱이어서"),
        (6, "앱을 사용할 시간이 없어서"),
        (7, "기타"),  # "기타" 선택지 추가
    ]
    # 탈퇴한 사용자 ID (외래키: User 모델 참조)
    user = models.ForeignKey(
        'User',  # User 모델 참조
        on_delete=models.CASCADE,  # User 삭제 시 관련 기록도 삭제
        related_name='deletions',
        verbose_name="탈퇴한 사용자"
    )
    reason = models.IntegerField(
        choices=REASON_CHOICES,
        verbose_name="탈퇴 사유"
    )  # 제공된 선택지에서 선택
    custom_reason = models.TextField(
        null=True, blank=True,
        verbose_name="기타 사유"
    )  # 사용자가 직접 입력한 기타 사유
    deleted_at = models.DateTimeField(
        default=now,
        verbose_name="탈퇴 날짜"
    )  # 탈퇴 날짜

    class Meta:
        db_table = "user_deletions"
        verbose_name = "사용자 탈퇴 기록"
        verbose_name_plural = "사용자 탈퇴 기록"

    def __str__(self):
        # "기타" 사유가 있는 경우, 상세 내용 표시
        if self.reason == 7 and self.custom_reason:
            return f"탈퇴 기록: {self.user.username} - 기타 사유: {self.custom_reason}"
        return f"탈퇴 기록: {self.user.username} - {self.get_reason_display()}"