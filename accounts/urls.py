from django.urls import path
from .views import *

urlpatterns = [
    # ✅ [공통] 회원가입 및 로그인 관련
    path('duplicate/', DuplicateIDView.as_view()),  # 아이디 중복 확인
    path('random/id/', RandomUsernameView.as_view()),  # 랜덤 아이디 생성
    path('random/nickname/', RandomNicknameView.as_view()),  # 랜덤 닉네임 생성

    # ✅ [공통] 유저 정보 관리
    path('refresh/', RefreshTokenView.as_view()), # 리프레시 토큰 리프레시
    path('update/id/', ChangeServiceIDView.as_view()),  # 아이디 변경
    path('update/pw/', ChangePasswordView.as_view()),  # 비밀번호 변경
    path('checkpw/', CheckPasswordView.as_view()), # 비밀번호 확인
    path('delete/', UserDeleteView.as_view()),  # 회원 탈퇴

    # ✅ [일반] 일반 회원가입 & 로그인
    path('consent/', ConsentView.as_view()), # 회원가입 전 약관 동의
    path('email/request/', RequestEmailVerificationView.as_view()),  # 이메일 인증 요청
    path('email/verify/', VerifyEmailView.as_view(), name='verify_email'), # 이메일 코드 입력 
    path('email/check/', CheckEmailVerificationView.as_view()),
    path('signup/', GeneralSignUpView.as_view()),  # 일반 회원가입
    path('login/', LogInView.as_view()),  # 일반 로그인
    
    # ✅ [소셜] 회원가입 & 로그인 관련
    path('social/signup/', SocialSignUpCompleteView.as_view()),  # 소셜 회원가입 설정 완료

    # ✅ [카카오] OAuth 회원가입 & 로그인
    path('kakao/', KakaoLoginView.as_view()),  # 카카오 로그인 페이지 이동
    path('kakao/callback/', KakaoCallbackView.as_view()),  # 카카오 로그인 콜백

    # ✅ [구글] OAuth 회원가입 & 로그인
    path("google/", GoogleLoginView.as_view()),
    path("google/callback/", GoogleCallbackView.as_view()),

    # ✅ [애플] OAuth 회원가입 & 로그인
    path("apple/", AppleLoginView.as_view()),
    path("apple/callback/", AppleCallbackView.as_view()),
]
