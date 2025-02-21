from django.shortcuts import render, get_object_or_404
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework import generics

#from rest_auth.registration.views import SocialLoginView                 
from allauth.socialaccount.providers.kakao import views as kakao_views     
from allauth.socialaccount.providers.oauth2.client import OAuth2Client  
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect

import WDYS
import requests
import allauth

#BASE_URL = 'http://127.0.0.1:8000/'
BASE_URL = 'http://localhost:8000/'

KAKAO_CONFIG = {
    "KAKAO_REST_API_KEY":getattr(WDYS.settings.base, 'KAKAO_CLIENT_ID', None),
    "KAKAO_REDIRECT_URI": "http://localhost:8000/accounts/kakao/callback/",
    "KAKAO_CLIENT_SECRET_KEY": getattr(WDYS.settings.base, 'KAKAO_CLIENT_SECRET_KEY', None), 
    #"KAKAO_PW":getattr(WDYS.settings.base, 'KAKAO_PW', None),
}
kakao_login_uri = "https://kauth.kakao.com/oauth/authorize"
kakao_token_uri = "https://kauth.kakao.com/oauth/token"
kakao_profile_uri = "https://kapi.kakao.com/v2/user/me"

# Create your views here.

# ✅ 약관 동의
class TermView(views.APIView):
    def post(self, request):
        # ✅ URL에서 signup_type 가져오기 (없으면 오류 처리)
        signup_type = request.GET.get("signup_type")
        if not signup_type:
            return Response({"error": "signup_type 값이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ POST 데이터 검증
        serializer = TermSerializer(data=request.data)
        if serializer.is_valid():
            required_consent = serializer.validated_data["required_consent"]
            push_notification_consent = serializer.validated_data["push_notification_consent"]
            marketing_consent = serializer.validated_data["marketing_consent"]

            # 세션에 약관 동의 정보 저장 (회원가입 단계에서 사용)
            request.session["signup_type"] = signup_type
            request.session["required_consent"] = required_consent
            request.session["push_notification_consent"] = push_notification_consent
            request.session["marketing_consent"] = marketing_consent

            # ✅ 다음 단계로 이동 (일반 회원가입 / 소셜 로그인)
            if signup_type == "general":
                return redirect("/accounts/signup/")  # 일반 회원가입 페이지로 이동
            elif signup_type == "kakao":
                return redirect("/accounts/kakao/")  # 카카오 로그인 처리
            #elif signup_type == "google":
            #    return redirect("/accounts/google/login/")  # 구글 로그인 처리
            #elif signup_type == "apple":
            #    return redirect("/accounts/apple/login/")  # 애플 로그인 처리

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ 회원가입
class SignUpView(views.APIView):
    serializer_class = SignUpSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message':'회원가입 성공', 'data':serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'message':'회원가입 실패', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ 로그인   
class LogInView(views.APIView):
    serializer_class= LogInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return Response({'message': "로그인 성공", 'data': serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({'message':'로그인 실패', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
# ✅ 아이디 중복 확인
class DuplicateIDView(views.APIView):
    def post(self, request):
        username = request.data.get('username')

        if User.objects.filter(username=username).exists():
            response_data = {'username':username,'아이디 중복 여부':True}
        else:
            response_data = {'username':username,'아이디 중복 여부':False}
        
        return Response(response_data, status=status.HTTP_200_OK)
    
# ✅ 아이디 변경
class ChangeUsernameView(views.APIView):
    serializer_class = UsernameUpdateSerializer

    def get(self, request, format=None):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def patch(self, request, format=None):
        serializer = UsernameUpdateSerializer(request.user, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '아이디 변경 성공.', 'data': serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({'message': '아이디 변경 실패.', 'data': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# ✅ 비밀번호 변경
class ChangePasswordView(views.APIView):
    serializer_class = PasswordUpdateSerializer

    def patch(self, request, format=None):
        serializer = PasswordUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            # 현재 비밀번호 확인
            if not user.check_password(current_password):
                return Response({'message': '현재 비밀번호가 옳지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # 새로운 비밀번호 설정
            user.set_password(new_password)
            user.save()

            return Response({'message': '비밀번호가 성공적으로 변경되었습니다.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': '올바르지 않은 데이터입니다.'}, status=status.HTTP_400_BAD_REQUEST)

# ✅ 회원 탈퇴
class UserDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        password = serializer.validated_data["password"]
        reason = serializer.validated_data["reason"]
        custom_reason = serializer.validated_data.get("custom_reason", "")

        # 비밀번호 확인
        if not user.check_password(password):
            return Response({"message": "접근 실패, 비밀번호가 옳지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 탈퇴 사유 저장
        UserDeletion.objects.create(
            user=user,
            reason=reason,
            custom_reason=custom_reason if reason == 7 else "",  # 기타 선택 시만 저장
            deleted_at=now()
        )

        # 유저 삭제
        user.delete()

        return Response({"message": "접근 성공. 회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK)



# ✅ 랜덤 아이디 추천
import random
import string

class RandomUsernameView(views.APIView):
    def get(self, request, *args, **kwargs):
        length = random.randint(6, 12)  # 6~12자 랜덤 길이
        chars = string.ascii_letters + string.digits + "_."
        
        max_attempts = 10  # 중복 방지를 위해 최대 10회 시도
        for _ in range(max_attempts):
            random_username = ''.join(random.choices(chars, k=length))
            if not User.objects.filter(username=random_username).exists():
                return Response({"random_username": random_username}, status=status.HTTP_200_OK)

        return Response({"error": "랜덤 아이디 생성에 실패했습니다. 다시 시도해주세요."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ 랜덤 닉네임 추천
class RandomNicknameView(views.APIView):
    def get(self, request, *args, **kwargs):
        serializer = RandomNicknameSerializer(data=request.GET)
        if serializer.is_valid():
            random_nickname = serializer.generate_random_nickname()
            return Response({"random_nickname": random_nickname}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# 💛 카카오
class KakaoLoginView(views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        client_id = KAKAO_CONFIG['KAKAO_REST_API_KEY']
        redirect_uri = KAKAO_CONFIG['KAKAO_REDIRECT_URI']

        uri = f"{kakao_login_uri}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
        
        res = redirect(uri)
        # res = requests.get(uri)
        print(res.get("access_tocken"))
        return res
    

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
        
class KUserDeleteView(views.APIView):
    def post(self, request):
        user = request.user
        user.delete()
        return Response({'message': '계정 삭제 성공'}, status=status.HTTP_204_NO_CONTENT)