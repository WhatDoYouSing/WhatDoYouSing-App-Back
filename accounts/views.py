from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.http import HttpResponse

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework import generics
              
from allauth.socialaccount.providers.kakao import views as kakao_views     
from allauth.socialaccount.providers.oauth2.client import OAuth2Client  
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView   

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from .serializers import *
from accounts.tokens import EmailVerificationTokenGenerator
from datetime import datetime

import hashlib
import base64
import WDYS
import requests
import allauth
import string
import os
import time
import jwt
from jwt.algorithms import RSAAlgorithm

BASE_URL = 'https://api.whatdoyousing.com/'

KAKAO_CONFIG = {
    "KAKAO_REST_API_KEY":getattr(WDYS.settings.base, 'KAKAO_CLIENT_ID', None),
    "KAKAO_REDIRECT_URI": "https://api.whatdoyousing.com/accounts/kakao/callback/",
    "KAKAO_CLIENT_SECRET_KEY": getattr(WDYS.settings.base, 'KAKAO_CLIENT_SECRET_KEY', None), 
}
kakao_login_uri = "https://kauth.kakao.com/oauth/authorize"
kakao_token_uri = "https://kauth.kakao.com/oauth/token"
kakao_profile_uri = "https://kapi.kakao.com/v2/user/me"

APPLE_BASE_URL = "https://appleid.apple.com"
APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

# 일반/소셜 공통, 유저 관리 ############################################################################################

# 📌 [애플] 보안 관련 토큰 설정
def verify_apple_id_token(id_token, client_id):
    res = requests.get(APPLE_KEYS_URL)
    keys = res.json().get("keys", [])
    client_id = settings.APPLE_CLIENT_ID
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")
    key = next((k for k in keys if k["kid"] == kid), None)
    if not key:
        raise ValueError("Apple public key not found")

    public_key = RSAAlgorithm.from_jwk(key)
    
    decoded = jwt.decode(
        id_token,
        key=public_key,
        algorithms=["RS256"],
        audience=client_id,
        issuer="https://appleid.apple.com"
    )
    return decoded

# ✅ [공통] 토큰 리프레시
class RefreshTokenView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        raw_refresh = request.data.get("refresh")
        if not raw_refresh:
            return Response({"message": "refresh 토큰이 필요합니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data  # {"access": "...", "refresh": "..."} or {"access": "..."}

        # 만료 시각 파싱
        access_token = data.get("access")
        access_exp_iso = None
        if access_token:
            at = AccessToken(access_token)
            access_exp_iso = datetime.fromtimestamp(at["exp"], tz=timezone.utc).isoformat()

        refresh_token = data.get("refresh")  # ROTATE_REFRESH_TOKENS=True일 때만 존재
        refresh_exp_iso = None
        if refresh_token:
            rt = RefreshToken(refresh_token)
            refresh_exp_iso = datetime.fromtimestamp(rt["exp"], tz=timezone.utc).isoformat()

        # 로그인 Serializer와 키 이름을 맞춤
        resp = {
            "access_token": access_token,
            "access_token_exp": access_exp_iso,
        }
        if refresh_token:
            resp.update({
                "refresh_token": refresh_token,
                "refresh_token_exp": refresh_exp_iso,
            })

        return Response(resp, status=status.HTTP_200_OK)
    
# 📌 [공통] 소셜 토큰 리턴
class SocialTokenView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")
        id_token = request.data.get("id_token")  # 구글/애플은 id_token도 가능

        if not provider or not access_token:
            return Response({"error": "provider와 access_token은 필수입니다."}, status=400)

        user_info = None

        if provider == "google":
            res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                               headers={"Authorization": f"Bearer {access_token}"})
            if res.status_code != 200:
                return Response({"error": "구글 토큰 검증 실패"}, status=400)
            profile = res.json()
            social_id = f"google_{profile['id']}"
            email = profile.get("email")
        
        elif provider == "kakao":
            res = requests.get("https://kapi.kakao.com/v2/user/me",
                               headers={"Authorization": f"Bearer {access_token}"})
            if res.status_code != 200:
                return Response({"error": "카카오 토큰 검증 실패"}, status=400)
            profile = res.json()
            social_id = f"kakao_{profile['id']}"
            email = profile.get("kakao_account", {}).get("email")

        elif provider == "apple":
            # ⚠️ 실제 운영에서는 애플 공개키 가져와 서명 검증 필수
            # decoded = jwt.decode(id_token, options={"verify_signature": False})

            # 📌 배포용 서명 검증
            decoded = verify_apple_id_token(id_token, settings.APPLE_CLIENT_ID)
            sub = decoded.get("sub")
            email = decoded.get("email")
            social_id = f"apple_{sub}"

        else:
            return Response({"error": "지원하지 않는 provider입니다."}, status=400)

        # --- User 조회/생성 ---
        try:
            user = User.objects.get(username=social_id)
        except User.DoesNotExist:
            user = User.objects.create(
                username=social_id,
                auth_provider=provider,
                auth_provider_email=email,
                is_active=True,
            )

        # --- JWT 발급 ---
        token = RefreshToken.for_user(user)
        resp = {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "profile": user.profile,
            "access_token": str(token.access_token),
            "access_token_exp": datetime.fromtimestamp(token.access_token['exp']),
            "refresh_token": str(token),
            "refresh_token_exp": datetime.fromtimestamp(token['exp']),
        }
        return Response(resp, status=200)

# ✅ [공통] 랜덤 아이디 추천
class RandomUsernameView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        length = random.randint(6, 12)  # 6~12자 랜덤 길이
        chars = string.ascii_letters + string.digits + "_."
        
        max_attempts = 10  # 중복 방지를 위해 최대 10회 시도
        for _ in range(max_attempts):
            random_username = ''.join(random.choices(chars, k=length))
            if not User.objects.filter(serviceID=random_username).exists():
                return Response({"random_username": random_username}, status=status.HTTP_200_OK)

        return Response({"error": "랜덤 아이디 생성에 실패했습니다. 다시 시도해주세요."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# ✅ [공통] 랜덤 닉네임 추천
class RandomNicknameView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        pattern = request.GET.get("pattern")
        serializer = RandomNicknameSerializer(data=request.GET)
        if serializer.is_valid():
            random_nickname = serializer.generate_random_nickname(pattern)
            return Response({"random_nickname": random_nickname}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ [공통] 아이디 중복 확인
class DuplicateIDView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serviceID = request.data.get('serviceID')

        if User.objects.filter(serviceID=serviceID).exists():
            response_data = {'duplicate': True}
        else:
            response_data = {'duplicate': False}
        
        return Response(response_data, status=status.HTTP_200_OK)

# ✅ [공통] 아이디 변경
class ChangeServiceIDView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceIDUpdateSerializer

    def get(self, request, format=None):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def patch(self, request):
        if not request.data: 
            return Response({'message': '입력이 없습니다'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(request.user, data=request.data, partial=True)
    
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '서비스 아이디 변경 성공', 'data': serializer.validated_data}, status=status.HTTP_200_OK)
    
        return Response({'message': '서비스 아이디 변경 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ [공통] 비밀번호 확인
class CheckPasswordView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user

            if user.auth_provider != "email":
                return Response({'message': '소셜 회원은 비밀번호를 변경할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            current_password = serializer.validated_data["current_password"]

            if not user.check_password(current_password):
                return Response({'message': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({'message': '비밀번호 확인 성공'}, status=status.HTTP_200_OK)

        return Response({'message': '입력값 오류', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
# ✅ [공통] 비밀번호 변경
class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            if not user.check_password(current_password):
                return Response({'message': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'message': '비밀번호 변경 성공'}, status=status.HTTP_200_OK)
        
        return Response({'message': '비밀번호 변경 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ [공통] 회원 탈퇴
class UserDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserDeleteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        auth_provider = user.auth_provider 
        reason_codes = serializer.validated_data["reason"]  # 리스트 형태
        custom_reason = serializer.validated_data.get("custom_reason", "")

        user_deletion = UserDeletion.objects.create(
            user=user,
            custom_reason=custom_reason,
            deleted_at=now()
        )

        reasons = WithdrawalReason.objects.filter(code__in=reason_codes)
        user_deletion.reason.set(reasons) 

        user_deletion.user = None
        user_deletion.save()

        if auth_provider == "email":
            VerifyEmail.objects.filter(email=user.email).delete()

        user.delete()

        return Response({"message": "회원 탈퇴 성공"}, status=status.HTTP_200_OK)

# 일반 유저 ############################################################################################

# ✅ [일반] 가입 약관 동의
class ConsentView(views.APIView):
    def post(self, request):
        serializer = ConsentSerializer(data=request.data)
        if serializer.is_valid():
            return Response({'message': '약관 동의 정보 확인 완료', 'data': serializer.validated_data}, status=200)
        return Response({'error': serializer.errors}, status=400)

# ✅ [일반] 이메일 인증 요청
class RequestEmailVerificationView(views.APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "이메일은 필수입니다."}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "이미 가입된 이메일입니다."}, status=400)

        code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timezone.timedelta(minutes=5)

        verify_obj, created = VerifyEmail.objects.update_or_create(
            email=email,
            defaults={"code": code, "is_verified": False, "expires_at": expires_at},
        )

        subject = "[왓두유씽] 이메일 인증 코드가 도착했어요!"
        html_content = render_to_string("email.html", {
            "code": code,
        })

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=f"인증 코드: {code}\n이 코드는 5분간 유효합니다.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return Response({"message": "인증 코드가 이메일로 발송되었습니다."}, status=200)

# ✅ [일반] 이메일 인증 처리
class VerifyEmailView(views.APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "이메일과 코드 모두 필요합니다."}, status=400)

        try:
            verify_obj = VerifyEmail.objects.get(email=email)
        except VerifyEmail.DoesNotExist:
            return Response({"error": "해당 이메일로 인증 요청이 없습니다."}, status=404)
        
        if verify_obj.is_expired():
            return Response({"error": "인증 코드가 만료되었습니다."}, status=400)

        if verify_obj.is_verified:
            return Response({"message": "이미 인증된 이메일입니다."}, status=200)

        if verify_obj.code != code:
            return Response({"error": "인증 코드가 일치하지 않습니다."}, status=400)

        # 인증 처리
        verify_obj.is_verified = True
        verify_obj.save()

        return Response({"message": "이메일 인증이 완료되었습니다."}, status=200)
    
# ✅ [일반] 이메일 인증 여부 확인
class CheckEmailVerificationView(views.APIView):
    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "이메일은 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verify_obj = VerifyEmail.objects.get(email=email)
        except VerifyEmail.DoesNotExist:
            return Response({"error": "인증 요청이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"is_verified": verify_obj.is_verified}, status=status.HTTP_200_OK)


# ✅ [일반] 회원가입
class GeneralSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = GeneralSignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data) 

        if serializer.is_valid():
            user = serializer.save()
            token_data = serializer.generate_tokens(user)
            return Response({'message': '회원가입 성공!', 'data': serializer.data, 'tokens': token_data}, status=status.HTTP_201_CREATED)
        return Response({'message': '회원가입 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ [일반] 로그인
class LogInView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LogInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return Response({'message': "로그인 성공", 'data': serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({'message': '로그인 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 소셜 유저 ############################################################################################

# ✅ [소셜] 회원가입 설정 마치기
class SocialSignUpCompleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        # 일반(이메일) 회원가입 유저는 접근 불가
        if user.auth_provider == "email":
            return Response({"message": "일반 회원가입 유저는 접근할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        # 소셜 회원가입 정보 업데이트
        serializer = SocialSignUpSerializer(instance=user, data=request.data, partial=True)

        if serializer.is_valid(): 
            serializer.save()
            return Response({'message': '소셜 회원가입 설정 완료', 'data': serializer.data}, status=status.HTTP_200_OK)

        return Response({'message': '설정 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 카카오 유저 ############################################################################################

# ✅ [카카오] 로그인 요청
class KakaoLoginView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """카카오 로그인 페이지로 리디렉션"""
        client_id = KAKAO_CONFIG["KAKAO_REST_API_KEY"]
        redirect_uri = KAKAO_CONFIG["KAKAO_REDIRECT_URI"]
        uri = f"{kakao_login_uri}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"

        return redirect(uri)

# ✅ [카카오] 로그인 콜백 (토큰 발급 후 사용자 정보 조회 및 회원가입/로그인)
class KakaoCallbackView(views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request):  
        data = request.query_params.copy()

        code = data.get('code')
        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        request_data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_CONFIG['KAKAO_REST_API_KEY'],
            'redirect_uri': KAKAO_CONFIG['KAKAO_REDIRECT_URI'],
            'client_secret': KAKAO_CONFIG['KAKAO_CLIENT_SECRET_KEY'],
            'code': code,
        }
        token_headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        token_res = requests.post(kakao_token_uri, data=request_data, headers=token_headers)

        token_json = token_res.json()
        access_token = token_json.get('access_token')

        if not access_token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        access_token = f"Bearer {access_token}" \

        # kakao 회원정보 요청
        auth_headers = {
            "Authorization": access_token,
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        user_info_res = requests.get(kakao_profile_uri, headers=auth_headers)
        user_info_json = user_info_res.json()

        social_type = 'kakao'
        social_id = f"{social_type}_{user_info_json.get('id')}"

        properties = user_info_json.get('properties',{})
        nickname=properties.get('nickname','')
        profile=properties.get('thumbnail_image_url','')
        print(user_info_json)

        # 회원가입 및 로그인 처리 
        try:   
            user_in_db = User.objects.get(username=social_id) 
            # kakao계정 아이디가 이미 가입한거라면 
            # 서비스에 rest-auth 로그인
            data={'username':social_id,'password':social_id}
            serializer = KLogInSerializer(data=data)
            if serializer.is_valid():
                return Response({'message': "카카오 로그인 성공", 'data': serializer.validated_data}, status=status.HTTP_200_OK)
            return Response({'message': "카카오 로그인 실패", 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:   
            # 회원 정보 없으면 회원가입 후 로그인
            # def post(self,request):
            print("회원가입")
            data={'username':social_id,'password':social_id,'nickname':nickname,'profile':profile}
            serializer=KSignUpSerializer(data=data)  
            if serializer.is_valid():
                serializer.save()                          # 회원가입
                data1={'username':social_id,'password':social_id}
                serializer1 = KLogInSerializer(data=data1)
                if serializer1.is_valid():
                    return Response({'message':'카카오 회원가입 성공','data':serializer1.validated_data}, status=status.HTTP_201_CREATED)
            return Response({'message':'카카오 회원가입 실패','error':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
# 구글 유저 ############################################################################################        

# ✅ [Google] 로그인 콜백 및 처리
class GoogleCallbackView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code missing'}, status=status.HTTP_400_BAD_REQUEST)

        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_SECRET
        redirect_uri = settings.GOOGLE_CALLBACK_URI
      
        # Access token 요청
        token_req_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        token_res = requests.post("https://oauth2.googleapis.com/token", data=token_req_data)
        token_json = token_res.json()
        access_token = token_json.get('access_token')
        if not access_token:
            return Response({'error': 'Access token retrieval failed'}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 정보 요청
        profile_res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                                   headers={"Authorization": f"Bearer {access_token}"})
        profile_json = profile_res.json()
        social_type = 'google'
        social_id = f"{social_type}_{profile_json.get('id')}"

        # 로그인 또는 회원가입
        try:
            user_in_db = User.objects.get(username=social_id)
            data = {'username': social_id, 'password': social_id}
            serializer = GLogInSerializer(data=data)
            if serializer.is_valid():
                return Response({'message': '구글 로그인 성공', 'data': serializer.validated_data}, status=status.HTTP_200_OK)
            return Response({'message': '구글 로그인 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            data = {'username':social_id,'password':social_id}
            serializer = GSignUpSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                data1 = {'username': social_id, 'password': social_id}
                serializer1 = GLogInSerializer(data=data1)
                if serializer1.is_valid():
                    return Response({'message': '구글 회원가입 성공', 'data': serializer1.validated_data}, status=status.HTTP_201_CREATED)
            return Response({'message': '구글 회원가입 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ [Google] 로그인 요청
class GoogleLoginView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        print("REDIRECT URI:", settings.GOOGLE_CALLBACK_URI)
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_CALLBACK_URI
        scope = "openid"
        response_type = "code"
        access_type = "offline"
        include_granted_scopes = "true"

        uri = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type={response_type}"
            f"&scope={scope}"
            f"&access_type={access_type}"
            f"&include_granted_scopes={include_granted_scopes}"
        )

        return redirect(uri)
    
# 애플 유저 ############################################################################################        

# ✅ [Apple] 로그인 요청
class AppleLoginView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        client_id = settings.APPLE_CLIENT_ID
        redirect_uri = settings.APPLE_REDIRECT_URI

        uri = (
            f"https://appleid.apple.com/auth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=name email"
            f"&response_mode=form_post"
        )

        return redirect(uri)

# 📌 [Apple] 로그인 콜백 및 처리
class AppleCallbackView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return self.get(request)

    def generate_client_secret(self):
        headers = {
            'alg': 'ES256',
            'kid': settings.APPLE_KEY_ID,
        }
        payload = {
            'iss': settings.APPLE_TEAM_ID,
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,
            'aud': "https://appleid.apple.com",
            'sub': settings.APPLE_CLIENT_ID,
        }

        client_secret = jwt.encode(
            payload,
            settings.APPLE_PRIVATE_KEY,
            algorithm='ES256',
            headers=headers
        )
        return client_secret

    def get(self, request):
        code = request.query_params.get("code") or request.data.get("code")
        if not code:
            return Response({'error': 'Authorization code missing'}, status=status.HTTP_400_BAD_REQUEST)

        client_secret = self.generate_client_secret()

        token_data = {
            'client_id': settings.APPLE_CLIENT_ID,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.APPLE_REDIRECT_URI,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_res = requests.post("https://appleid.apple.com/auth/token", data=token_data, headers=headers)
        token_json = token_res.json()

        id_token = token_json.get("id_token")
        if not id_token:
            return Response({'error': 'id_token missing'}, status=status.HTTP_400_BAD_REQUEST)

        # ⚠️ 서명 검증 비활성화 (개발용)
        # decoded = jwt.decode(id_token, options={"verify_signature": False})

        # 📌 서명 검증 활성화 (배포용)
        decoded = verify_apple_id_token(id_token, settings.APPLE_CLIENT_ID)
        sub = decoded.get("sub")
        email = decoded.get("email")

        if not sub or not email:
            return Response({'error': 'Invalid id_token'}, status=status.HTTP_400_BAD_REQUEST)

        # 로그인 or 회원가입
        social_type = 'apple'
        social_id = f"{social_type}_{sub}"

        try:
            user = User.objects.get(username=social_id)
            data = {'username': social_id, 'password': social_id}
            serializer = ALogInSerializer(data=data)
            if serializer.is_valid():
                return Response({'message': '애플 로그인 성공', 'data': serializer.validated_data}, status=status.HTTP_200_OK)
            return Response({'message': '애플 로그인 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            data = {'username': social_id, 'password': social_id}
            serializer = ASignUpSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                serializer2 = ALogInSerializer(data=data)
                if serializer2.is_valid():
                    return Response({'message': '애플 회원가입 성공', 'data': serializer2.validated_data}, status=status.HTTP_201_CREATED)
            return Response({'message': '애플 회원가입 실패', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
