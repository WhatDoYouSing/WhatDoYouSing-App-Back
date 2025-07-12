from django.shortcuts import render, get_object_or_404
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework import generics
from datetime import datetime
from django.db.models import Max
from django.utils.dateparse import parse_date

# Create your views here.

# ✅ [마이페이지] 기본 정보
class MyPageView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyPageSerializer

    def get(self, request):
        serializer=self.serializer_class(request.user)
        return Response({'message': '마이페이지 조회 성공', 'data': serializer.data}, status=status.HTTP_200_OK)

# ✅ [마이페이지] 통합/노트/플리 가져오기
class MyContentView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        content_type = request.query_params.get("type", None)
        date_str = request.query_params.get("date", None)
        user = request.user

        date_filter = None
        if date_str:
            date_filter = parse_date(date_str)  # "YYYY-MM-DD" → date 객체 변환
            if not date_filter:
                return Response({"message": "잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        notes = Notes.objects.filter(user=user).order_by('-created_at')
        plis = Plis.objects.filter(user=user).order_by('-created_at')

        if date_filter:
            notes = notes.filter(created_at__date=date_filter)  # ✅ 해당 날짜의 노트만 필터링
            plis = plis.filter(created_at__date=date_filter)  # ✅ 해당 날짜의 플리만 필터링

        if content_type == "note":
            serializer = MyNoteSerializer(notes, many=True)
            return Response(serializer.data)

        elif content_type == "pli":
            serializer = MyPliSerializer(plis, many=True)
            return Response(serializer.data)

        # ✅ content_type이 없으면 모든 데이터 합쳐서 정렬 후 반환
        combined_content = list(notes) + list(plis)
        combined_content.sort(key=lambda x: x.created_at, reverse=True)

        serialized_data = []
        for content in combined_content:
            if isinstance(content, Notes):
                serialized_data.append(MyNoteSerializer(content).data)
            elif isinstance(content, Plis):
                serialized_data.append(MyPliSerializer(content).data)

        return Response(serialized_data, status=status.HTTP_200_OK)

# ✅ [마이페이지] 칭호 전부 가져오기 + 각 칭호 활성화 여부
class TitleListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        titles = Title.objects.all()
        serializer = TitleListSerializer(titles,many=True, context={'user': request.user})
        return Response({'message': '칭호 목록 조회 성공', 'data': serializer.data}, status=status.HTTP_200_OK)

# ✅ [마이페이지-내 프로필 편집] 활성화 칭호 중 프로필 이미지만 get 해오기 + 선택하기
class ProfileChoiceView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_titles = UserTitle.objects.filter(user=request.user).select_related('title')
        emojis = [title.title.emoji for title in active_titles]
        return Response({'message': '활성화된 칭호의 프로필 목록 조회 성공', 'data': emojis}, status=status.HTTP_200_OK)

    def patch(self, request):
        new_emoji = request.data.get('emoji')
        if new_emoji is None:
            return Response({'message': '이모지 값이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        active_emojis = [title.title.emoji for title in UserTitle.objects.filter(user=request.user)]
        if new_emoji not in active_emojis:
            return Response({'message': '선택한 프로필은 활성화된 칭호에 해당하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.profile = new_emoji
        request.user.save()
        return Response({'message': '프로필 이미지 변경 성공'}, status=status.HTTP_200_OK)

# ✅ [마이페이지-내 칭호 편집] 활성화 칭호 중 칭호만 get 해오기 + 선택하기
class TitleChoiceView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_titles = UserTitle.objects.filter(user=request.user).select_related('title')
        serializer = ActiveUserTitleSerializer(active_titles, many=True)
        return Response({'message': '활성화된 칭호 조회 성공', 'data': serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request):
        new_title_id = request.data.get('title_id')
        if not new_title_id:
            return Response({'message': '칭호 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_title = Title.objects.get(id=new_title_id)
            if not UserTitle.objects.filter(user=request.user, title=new_title).exists():
                return Response({'message': '해당 칭호가 활성화되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            request.user.title_selection = new_title
            request.user.save()
            return Response({'message': '칭호 변경 성공'}, status=status.HTTP_200_OK)

        except Title.DoesNotExist:
            return Response({'message': '존재하지 않는 칭호입니다.'}, status=status.HTTP_404_NOT_FOUND)

# ✅ [마이페이지] 닉네임 변경
class NicknameUpdateView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NicknameUpdateSerializer

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

# 📌 [마이페이지] 달력 뷰
class MyCalendarView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        user = request.user

        if not year or not month:
            return Response({"message": "연도와 월이 필요합니다. (예: ?year=2025&month=03)"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, month = int(year), int(month)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response({"message": "올바른 연도와 월을 입력해주세요. (예: ?year=2025&month=03)"}, status=status.HTTP_400_BAD_REQUEST)

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        notes = Notes.objects.filter(user=user, created_at__range=[start_date, end_date])
        plis = Plis.objects.filter(user=user, created_at__range=[start_date, end_date])

        content_by_date = {}

        all_contents = list(notes) + list(plis)
        all_contents.sort(key=lambda x: x.created_at, reverse=True)  # 최신순 정렬

        for content in all_contents:
            date_key = content.created_at.strftime("%Y-%m-%d")  # YYYY-MM-DD 형식
            if date_key not in content_by_date:
                if isinstance(content, Notes):
                    content_by_date[date_key] = NoteThumbnailSerializer(content).data
                elif isinstance(content, Plis):
                    content_by_date[date_key] = PliThumbnailSerializer(content).data

        return Response(
            {"message": "달력 데이터 조회 성공", "data": content_by_date}, 
            status=status.HTTP_200_OK
        )