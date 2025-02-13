from django.shortcuts import render
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework import generics

# Create your views here.

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