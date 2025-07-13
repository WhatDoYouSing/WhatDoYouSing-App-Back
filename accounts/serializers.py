from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import *
import random

User = get_user_model()

# 일반/소셜 공통, 유저 관리 ############################################################################################

# ✅ 회원가입 공통 부모 Serializer
class AbstractSignupSerializer(serializers.ModelSerializer):
    """일반 및 소셜 회원가입 공통 필드"""

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname']

# ✅ 유저 serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile"]

# ✅ 랜덤 닉네임 Serializer
ADJECTIVES = [
    "멋진", "행복한", "슬픈", "낭만적인", "감상적인", "설레는", "희망찬", "센치한", "벅차는", "비장한",
    "신나는", "그리운", "평온한", "잔잔한", "정열적인", "빠른", "위대한", "천재적인", "독창적인", "혁신적인",
    "감동적인", "뛰어난", "훌륭한", "정교한", "독보적인", "창의적인", "심오한", "감각적인", "섬세한", "풍부한",
    "신비로운", "아름다운", "감미로운", "우아한", "인상적인", "강렬한", "차분한", "다채로운", "명료한", "세련된",
    "대담한", "순수한", "고요한", "따뜻한", "기품있는", "진지한", "자유로운", "영예로운", "매력적인", "용감한",
    "찬란한", "고상한", "고귀한", "절묘한", "매혹적인", "명석한", "예리한", "단아한", "여유로운", "빛나는",
    "눈부신", "기쁜", "현대적인", "고풍스러운", "활기찬", "고전적인", "향기로운", "탁월한", "빼어난", "묘한",
    "우렁찬", "정직한", "소박한", "유쾌한", "활발한", "애틋한", "다정한", "근사한", "새로운", "자연스러운",
    "기운찬", "부드러운", "간결한", "원숙한", "안정적인", "놀라운", "완벽한", "경이로운", "따스한", "힘찬",
    "진실된", "명확한", "경쾌한", "조화로운", "유연한", "기발한", "도전적인", "특별한", "편안한", "유려한",
    "갸냘픈", "거센", "고른", "고마운", "고운", "괜찮은", "구석진", "귀여운", "그리운", "기쁜", "깊은",
    "깨끗한", "나은", "난데없는", "네모난", "느닷없는", "느린", "동그란", "둥근", "뛰어난", "밝은", "보람찬",
    "빠른", "뽀얀", "새로운", "성가신", "수줍은", "쏜살같은", "알맞은", "엄청난", "여문", "예쁜", "작은",
    "재미있는", "점잖은", "좋은", "즐거운", "지혜로운", "짓궂은", "한결같은", "희망찬", "힘찬"
]
NOUNS = [
    "베토벤", "모차르트", "바흐", "쇼팽", "드뷔시", "브람스", "비발디", "슈만", "차이콥스키", "엘가",
    "푸치니", "말러", "헨델", "마쇼", "란디니", "뒤페", "프레", "탈리스", "랏소", "제수알도",
    "가브리엘", "몬테베르디", "쉬츠", "륄리", "북스테후데", "파헬벨", "퍼셀", "쿠프랭", "라모", "텔레만",
    "글룩", "하이든", "파가니니", "폰베버", "로시니", "슈베르트", "도니제티", "벨리니", "베를리오즈", "글린카",
    "멘델스존", "리스트", "바그너", "구노", "오펜바흐", "프랑크", "랄로", "스메타나", "브루크너", "슈트라우스",
    "보로딘", "생상스", "브루흐", "비제", "무소르그스키", "드보르자크", "그리그", "사라사테", "림스키", "포레",
    "볼프", "알베니스", "글라주노프", "시벨리우스", "사티", "스크랴빈", "윌리엄스", "라흐마니노프", "홀스트", "라벨",
    "파야", "레스피기", "야나체크", "쇤베르크", "아이브스", "버르토크", "스트라빈스키", "코다이", "베베른", "베르크",
    "프로코피예프", "힌데미트", "거슈윈", "코플랜드", "로드리고", "쇼스타코비치", "메시앙", "케이지", "브리튼", "피아졸라",
    "노노", "슈톡하우젠", "바렌보임", "오르프", "불레즈", "길렐스", "에밀", "알캉", "고도프스키", "이자이"
]
NUMBERS = [str(i).zfill(3) for i in range(1000)]  # 000 ~ 999
PATTERNS = ["adjective_noun", "noun_number", "adjective_noun_number"]

# ✅ 랜덤 닉네임 Serializer
class RandomNicknameSerializer(serializers.Serializer):
    pattern = serializers.ChoiceField(choices=PATTERNS, required=False)

    def generate_random_nickname(self, pattern):
        pattern = random.choice(PATTERNS)
        max_attempts = 10  # 9자 이하의 닉네임을 찾기 위한 최대 시도 횟수

        for _ in range(max_attempts):
            if pattern == "adjective_noun":
                nickname = random.choice(ADJECTIVES) + random.choice(NOUNS)
            elif pattern == "noun_number":
                nickname = random.choice(NOUNS) + random.choice(NUMBERS)
            else:
                nickname = random.choice(ADJECTIVES) + random.choice(NOUNS) + random.choice(NUMBERS)

            if len(nickname) <= 9:
                return nickname
        return nickname[:9]  # 9자 이하 유지

# ✅ 유저 아이디 변경 Serializer
class ServiceIDUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','serviceID']

# ✅ 유저 비밀번호 변경 serializer
class PasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)
    
# ✅ 유저 탈퇴 serializer    
class UserDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, write_only=True,  style={'input_type': 'password'}, required=False)
    reason = serializers.ChoiceField(choices=UserDeletion.REASON_CHOICES, required=True)
    custom_reason = serializers.CharField(required=False, allow_blank=True)
    confirm_delete = serializers.BooleanField(required=True)

    def validate(self, data):
        user = self.context['request'].user

        if not data.get("confirm_delete"):
            raise serializers.ValidationError({"confirm_delete": "탈퇴를 진행하려면 동의해야 합니다."})

        if data["reason"] == 7 and not data.get("custom_reason"):
            raise serializers.ValidationError({"custom_reason": "기타 사유를 입력해야 합니다."})

        if user.auth_provider == "email" and "password" not in data:
            raise serializers.ValidationError({"password": "일반 회원은 비밀번호를 입력해야 합니다."})

        return data  

# 일반 유저 ############################################################################################

# ✅ 일반 회원가입 약관 동의 Serializer
class ConsentSerializer(serializers.Serializer):
    required_consent = serializers.BooleanField()
    push_notification_consent = serializers.BooleanField(default=False)
    marketing_consent = serializers.BooleanField(default=False)

    def validate_required_consent(self, value):
        if not value:
            raise serializers.ValidationError("필수 약관에 동의해야 회원가입을 진행할 수 있습니다.")
        return value

# ✅ 일반 회원가입 Serializer
class GeneralSignUpSerializer(AbstractSignupSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    required_consent = serializers.BooleanField()
    push_notification_consent = serializers.BooleanField(default=False)
    marketing_consent = serializers.BooleanField(default=False)

    class Meta(AbstractSignupSerializer.Meta):
        fields = AbstractSignupSerializer.Meta.fields + [
            'email', 'password', 'required_consent', 'push_notification_consent', 'marketing_consent'
        ]

    def validate_required_consent(self, value):
        if value is not True:
            raise serializers.ValidationError("필수 약관에 동의해야 합니다.")
        return value

    def create(self, validated_data):
        first_title = Title.objects.first()
        if not validated_data.get('title') and first_title:
            validated_data['title'] = first_title.name  # 기본 칭호 적용

        user = User(
            username=validated_data['username'],
            serviceID=validated_data['username'], 
            email=validated_data['email'],
            nickname=validated_data['nickname'],
            required_consent=validated_data['required_consent'],
            push_notification_consent=validated_data.get('push_notification_consent', False),
            marketing_consent=validated_data.get('marketing_consent', False)
        )
        user.is_active=False
        user.set_password(validated_data['password'])  # 비밀번호 해싱
        user.save()
        return user



# ✅ 일반 로그인 Serializer
class LogInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email:
            raise serializers.ValidationError('이메일을 입력해주세요.')
        if not password:
            raise serializers.ValidationError('비밀번호를 입력해주세요.')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 사용자입니다.')

        if not user.check_password(password):
            raise serializers.ValidationError('잘못된 비밀번호입니다.')

        return self.generate_tokens(user)

    def generate_tokens(self, user):
        """토큰 생성"""
        token = RefreshToken.for_user(user)
        return {
            'id': user.id,
            'email': user.email,
            'nickname': user.nickname,
            'profile': user.profile,
            #'title': TitleSerializer(user.title).data if user.title else None,  # 칭호 추가
            'access_token': str(token.access_token),
            'refresh_token': str(token),
        }

# 소셜 공통 ############################################################################################    
    
# ✅ 소셜 회원가입 Serializer
class SocialSignUpSerializer(serializers.ModelSerializer):
    """소셜 회원가입 완료 Serializer (2차 정보 입력)"""
    required_consent = serializers.BooleanField()  # ✅ 필수 약관 동의
    push_notification_consent = serializers.BooleanField(default=False)  # ✅ 푸시 알림 동의
    marketing_consent = serializers.BooleanField(default=False)  # ✅ 마케팅 동의
    serviceID = serializers.CharField(required=True)  # ✅ 사이트 내에서 사용할 아이디
    nickname = serializers.CharField(required=True)  # ✅ 닉네임

    class Meta:
        model = User
        fields = [
            'serviceID', 'nickname', 'required_consent',
            'push_notification_consent', 'marketing_consent'
        ]

    def validate_required_consent(self, value):
        """필수 약관 동의 검증"""
        if value is not True:
            raise serializers.ValidationError("필수 약관에 동의해야 합니다.")
        return value

    def update(self, instance, validated_data):
        """소셜 회원가입 정보 업데이트 (2차 정보 입력)"""
        first_title = Title.objects.first()

        instance.serviceID = validated_data.get('serviceID')
        instance.nickname = validated_data.get('nickname')
        instance.required_consent = validated_data['required_consent']
        instance.push_notification_consent = validated_data.get('push_notification_consent', False)
        instance.marketing_consent = validated_data.get('marketing_consent', False)
        if not instance.title and first_title:
            instance.title = first_title.name  # 기본 칭호 자동 설정

        instance.save()
        return instance


# 카카오 유저 ############################################################################################

# ✅ 카카오 회원가입 Serializer
class KSignUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            auth_provider="kakao",
        )
        user.set_password(validated_data['password'])  # 비밀번호 해싱
        user.save()

        return user

# ✅ 카카오 로그인 Serializer    
class KLogInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        username=data.get("username", None)
        password=data.get("password", None)

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)

            if not user.check_password(password):
                raise serializers.ValidationError('잘못된 비밀번호입니다.')
            else:
                token = RefreshToken.for_user(user)
                refresh = str(token)
                access = str(token.access_token)

                data = {
                    'id': user.id,
                    'username':user.username,
                    'nickname': user.nickname,
                    'profile':user.profile,
                    'access_token': access,
                    'refresh_token': refresh,
                }

                return data
        else: 
            raise serializers.ValidationError('존재하지 않는 사용자입니다.')
        
# 구글 유저 ############################################################################################

# 📌 구글 회원가입 Serializer
# GSignUpSerializer
class GSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            auth_provider="google",
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# 📌 구글 로그인 Serializer
class GLogInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 사용자입니다.')

        if not user.check_password(password):
            raise serializers.ValidationError('잘못된 비밀번호입니다.')

        token = RefreshToken.for_user(user)
        return {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'profile': user.profile,
            'access_token': str(token.access_token),
            'refresh_token': str(token),
        }