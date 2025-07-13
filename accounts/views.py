from django.shortcuts import render, get_object_or_404
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework import generics
from accounts.tokens import EmailVerificationTokenGenerator

from dj_rest_auth.registration.views import SocialLoginView                 
from allauth.socialaccount.providers.kakao import views as kakao_views     
from allauth.socialaccount.providers.oauth2.client import OAuth2Client  
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string

import hashlib
import base64
import WDYS
import requests
import allauth
import string

BASE_URL = 'http://localhost:8000/'

KAKAO_CONFIG = {
    "KAKAO_REST_API_KEY":getattr(WDYS.settings.base, 'KAKAO_CLIENT_ID', None),
    "KAKAO_REDIRECT_URI": "http://localhost:8000/accounts/kakao/callback/",
    "KAKAO_CLIENT_SECRET_KEY": getattr(WDYS.settings.base, 'KAKAO_CLIENT_SECRET_KEY', None), 
}
kakao_login_uri = "https://kauth.kakao.com/oauth/authorize"
kakao_token_uri = "https://kauth.kakao.com/oauth/token"
kakao_profile_uri = "https://kapi.kakao.com/v2/user/me"

# Create your views here.

# 일반/소셜 공통, 유저 관리 ############################################################################################

# ✅ [공통] 랜덤 아이디 추천
class RandomUsernameView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        length = random.randint(6, 12)  # 6~12자 랜덤 길이
        chars = string.ascii_letters + string.digits + "_."
        
        max_attempts = 10  # 중복 방지를 위해 최대 10회 시도
        for _ in range(max_attempts):
            random_username = ''.join(random.choices(chars, k=length))
            if not User.objects.filter(username=random_username).exists():
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

    def get(self, request):
        user = request.user
        auth_provider = user.auth_provider
        return Response({"user type":auth_provider})

    def post(self, request):
        serializer = UserDeleteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        auth_provider = user.auth_provider 
        reason = serializer.validated_data["reason"]
        custom_reason = serializer.validated_data.get("custom_reason", "")

        if auth_provider == "email":
            password = serializer.validated_data["password"]
            if not user.check_password(password):
                return Response({"message": "비밀번호가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user_deletion = UserDeletion.objects.create(
            user=user,
            reason=reason,
            custom_reason=custom_reason if reason == 7 else "",
            deleted_at=now()
        )

        user_deletion.user = None
        user_deletion.save()

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

# ✅ [일반] 이메일 인증 요청 (최종)
class RequestEmailVerificationView(views.APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "이메일은 필수입니다."}, status=400)

        # 이미 존재하는 유저가 있다면 거부해도 됨
        if User.objects.filter(email=email).exists():
            return Response({"error": "이미 가입된 이메일입니다."}, status=400)

        # 토큰 생성
        token = EmailVerificationTokenGenerator().make_token(email)
        uid = urlsafe_base64_encode(force_bytes(email))

        verification_link = request.build_absolute_uri(
            reverse("verify_email", kwargs={"uidb64": uid, "token": token})
        )

        subject = "[왓두유씽] 이메일 주소 인증이 도착했어요!"
        
        html_content = render_to_string("email.html", {
            "verification_link": verification_link,
        })

        email_message = EmailMultiAlternatives(
            subject=subject,
            body="HTML 지원되지 않는 클라이언트를 위한 텍스트 버전입니다.",  # fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return Response({"message": "인증 메일이 발송되었습니다."}, status=200)
    
# ✅ [일반] 이메일 인증
class VerifyEmailView(views.APIView):
    def get(self, request, uidb64, token):
        try:
            email = force_str(urlsafe_base64_decode(uidb64))
        except (ValueError, TypeError, OverflowError):
            return Response({'error': '유효하지 않은 링크입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 토큰 확인
        token_valid = EmailVerificationTokenGenerator().check_token(email, token)
        if not token_valid:
            return Response({'error': '토큰이 유효하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 프론트에서 이 이메일로 본가입 진행하도록 안내
        return Response({
            'message': '이메일 인증이 완료되었습니다. 회원가입을 계속 진행해주세요!',
            'email': email
        }, status=status.HTTP_200_OK)

# ✅ [일반] 회원가입
class GeneralSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = GeneralSignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            self.send_verification(request,user)
            return Response({'message': '회원가입 성공! 이메일 인증 메일 확인 시 계정이 활성화 됩니다', 'data': serializer.data}, status=status.HTTP_201_CREATED)
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

# 📌 [Google] 로그인 콜백 및 처리
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
        #email = profile_json.get('email')
        #nickname = profile_json.get('name', '')
        #profile = 0

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

# [Google] 로그인 요청
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