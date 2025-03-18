from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser

class Title(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name="칭호 이름")  # 칭호 이름
    condition = models.TextField(null=False, verbose_name="칭호 조건")  # 칭호 조건
    emoji = models.IntegerField(default=0, verbose_name="칭호 이모지")  # 칭호 이모지 ID

    class Meta:
        db_table = "titles"  # 테이블 이름
        verbose_name = "칭호"
        verbose_name_plural = "칭호"

    def __str__(self):
        return self.name  # 관리자 페이지 등에서 이름으로 표시
 
class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="이메일 주소")
    username = models.CharField(max_length=150, unique=True, verbose_name="아이디")
    serviceID = models.CharField(max_length=150, unique=True, verbose_name="서비스 내 아이디",null=True,blank=True)
    notif_token = models.TextField(null=True, blank=True, verbose_name="FCM 토큰")
    nickname = models.CharField(max_length=50, verbose_name="닉네임")
    profile = models.IntegerField(default=0, verbose_name="프로필")
    title = models.CharField(max_length=100,null=True,blank=True,verbose_name="칭호")
    # 소셜 로그인 제공자 선택 (애플, 카카오, 구글)
    auth_provider = models.CharField(
        max_length=50,
        choices=[
            ("apple", "Apple"),
            ("kakao", "Kakao"),
            ("google", "Google"),
            ("email", "Email"),
        ],
        default="email"
        #verbose_name="소셜 로그인 제공자"
    )
    #auth_provider_id = models.CharField(max_length=255, verbose_name="소셜 로그인 사용자 ID")
    auth_provider_email = models.EmailField(unique=True, null=True, blank=True, verbose_name="소셜 로그인 이메일")
    required_consent = models.BooleanField(default=False, verbose_name="필수 약관 동의 여부")
    push_notification_consent = models.BooleanField(default=False, verbose_name="푸시알림 동의 여부")
    marketing_consent = models.BooleanField(default=False, verbose_name="마케팅 정보 수신 동의 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="계정 생성 날짜")
    last_use_at = models.DateTimeField(default=now, verbose_name="마지막 접속 날짜")
    
    class Meta:
        db_table = "users"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"
    
    def save(self, *args, **kwargs):
        if self.auth_provider == "email":
            self.auth_provider_email = self.email  # ✅ 일반 유저는 auth_provider_email을 자신의 email로 설정

        if self.pk is None:  # 새로운 유저 생성 시에만 실행
            first_title = Title.objects.first()
            if first_title:
                self.profile = self.profile or first_title.emoji  # 기본값 설정
                self.title = self.title or first_title.name  # 칭호 이름으로 저장하도록 변경
        super().save(*args, **kwargs)

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
        (7, "기타"),  # "기 선택지 추가
    ]
    # 탈퇴한 사용자 ID (외래키: User 모델 참조)
    user = models.ForeignKey(
        'User',  # User 모델 참조
        on_delete=models.CASCADE,  # User 삭제 시 관련 기록도 삭제
        related_name='deletions',
        verbose_name="탈퇴한 사용자"
    )

    '''
    탈퇴한 유저의 기록을 즉시 삭제하지 않을 거라면 이걸로 변경 필요
    user = models.ForeignKey(
    'User',
    null=True,  # 탈퇴 후에도 기록을 남기기 위해 null 허용
    blank=True,
    on_delete=models.SET_NULL,
    related_name='deletions',
    verbose_name="탈퇴한 사용자"
    )

    '''
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

class UserTitle(models.Model):
    user = models.ForeignKey(
        User,  # 같은 파일 내 User 모델 직접 참조
        on_delete=models.CASCADE,
        related_name="user_titles",  # 역참조 이름
        verbose_name="유저"
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="user_titles",  # 역참조 이름
        verbose_name="칭호"
    )
    #is_active = models.BooleanField(default=False, verbose_name="활성화 여부")  # 현재 활성화된 칭호인지
    acquired_at = models.DateTimeField(default=now, verbose_name="획득 날짜")  # 칭호 획득 날짜

    class Meta:
        db_table = "user_titles"  # 테이블 이름
        verbose_name = "유저 획득 칭호"
        verbose_name_plural = "유저 획득 칭호"
        unique_together = ("user", "title")  # 동일 유저-칭호 중복 저장 방지

    def __str__(self):
        return f"{self.user.username} - {self.title.name}"  # 유저와 칭호 이름 표시
