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
    email = models.EmailField(unique=True, verbose_name="이메일 주소", null=True, blank=True)
    username = models.CharField(max_length=150, unique=True, verbose_name="아이디")
    serviceID = models.CharField(max_length=150, unique=True, verbose_name="서비스 내 아이디",null=True,blank=True)
    notif_token = models.TextField(null=True, blank=True, verbose_name="FCM 토큰")
    nickname = models.CharField(max_length=50, verbose_name="닉네임", null=True, blank=True)
    profile = models.IntegerField(default=0, verbose_name="프로필", null=True, blank=True)
    title_selection = models.ForeignKey(Title, on_delete=models.CASCADE, verbose_name="현재 칭호", null=True, blank=True)

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
        '''
        if self.pk is None:  # 새로운 유저 생성 시
            blank_title = Title.objects.get(name="blank")
            UserTitle.objects.get_or_create(user=self, title=blank_title)
            self.title_selection = blank_title
            self.profile = self.profile or blank_title.emoji
        '''
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class WithdrawalReason(models.Model):
    code = models.IntegerField(unique=True)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label    

class UserDeletion(models.Model):
    #REASON_CHOICES = [
    #    (1, "다른 사용자들의 콘텐츠가 부족해서"),
    #    (2, "올리고 싶은 콘텐츠가 적어서"),
    #    (3, "기능 사용 방법이 편리하지 않아서"),
    #    (4, "원하는 기능이 없어서"),
    #    (5, "호기심에 설치한 앱이어서"),
    #    (6, "앱을 사용할 시간이 없어서"),
    #    (7, "기타"),
    #]
    # 탈퇴한 사용자 ID (외래키: User 모델 참조)
    user = models.ForeignKey(
        'User',  # User 모델 참조
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # User 삭제 시 해당 필드만 null이 되도록
        related_name='deletions',
        verbose_name="탈퇴한 사용자"
    )

    #reason = models.IntegerField(
    #    choices=REASON_CHOICES,
    #    verbose_name="탈퇴 사유"
    #)
    reason = models.ManyToManyField(WithdrawalReason)
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
        user_str = self.user.username if self.user else "탈퇴한 유저"
        return f"{user_str} (사유: {self.reason})"

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
    acquired_at = models.DateTimeField(default=now, verbose_name="획득 날짜")  # 칭호 획득 날짜

    class Meta:
        db_table = "user_titles"  # 테이블 이름
        verbose_name = "유저 획득 칭호"
        verbose_name_plural = "유저 획득 칭호"
        unique_together = ("user", "title")  # 동일 유저-칭호 중복 저장 방지

    def __str__(self):
        return f"{self.user.username} - {self.title.name}"  # 유저와 칭호 이름 표시
    
class VerifyEmail(models.Model):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
