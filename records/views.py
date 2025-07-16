from django.shortcuts import render, get_object_or_404
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework import generics
from datetime import datetime
from django.db.models import Max
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from collections import OrderedDict, defaultdict
from django.db.models import F 

# Create your views here.

# ✅ [레코드] 메인 화면 앨범아트 가져오기 (최신순 10개)
class MainRecordView(generics.ListAPIView):
    serializer_class = MainRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Notes.objects
            .filter(user=user)
            .only('album_art')   
            .order_by('-created_at')[:10]   # 최신 10개
        )

# ✅ [레코드] 감정시집
class EmotionsRecordView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user        = request.user
        date_str    = request.query_params.get("date")  
        emotion_str = request.query_params.get("emo")   

        qs = Notes.objects.filter(user=user).select_related("emotion")

        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m")
            except ValueError:
                raise ValidationError(
                    {"message": "잘못된 형식입니다. YYYY-MM 형식으로 입력해주세요."}
                )
            qs = qs.filter(created_at__year=dt.year,
                           created_at__month=dt.month)

        if emotion_str:
            qs = qs.filter(emotion__name=emotion_str)

            qs = qs.order_by("created_at")        
            data = {
                "month": date_str,
                "emotion": emotion_str,
                "notes": EmotionsRecordSerializer(qs, many=True).data
            }
            return Response(data, status=status.HTTP_200_OK)

        qs = qs.order_by("emotion__id", "created_at")

        grouped = OrderedDict()
        for note in qs:
            key = note.emotion.name if note.emotion else "unknown"
            grouped.setdefault(key, []).append(note)

        sorted_groups = sorted(grouped.items(),
                               key=lambda item: len(item[1]),
                               reverse=True)

        response_data = [
            {
                "month": date_str,
                "emotion": emotion_name,
                "notes": EmotionsRecordSerializer(notes, many=True).data
            }
            for emotion_name, notes in sorted_groups
        ]
        return Response(response_data, status=status.HTTP_200_OK)
    
# 📌 [레코드] 단어모음집
class WordTopView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = WordStatSerializer

    def get_queryset(self):
        user = self.request.user
        date_str = self.request.query_params.get("date")
        if not date_str:
            raise ValidationError({"message": "date 파라미터가 필요합니다. (YYYY-MM)"})
        try:
            dt = datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            raise ValidationError({"message": "YYYY-MM 형식이 아닙니다."})

        return (
            WordStat.objects
            .filter(user=user, year=dt.year, month=dt.month)
            .order_by("-count")[:10] 
        )

class WordDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = NoteThumbSerializer

    def get_queryset(self):
        user      = self.request.user
        date_str  = self.request.query_params.get("date")
        noun      = self.kwargs["word"].lower()

        if not date_str:
            raise ValidationError({"message": "date 파라미터가 필요합니다. (YYYY-MM)"})
        dt = datetime.strptime(date_str, "%Y-%m")

        # 해당 월에 사용자 노트 중 noun 포함된 ID 추출
        note_ids = (
            NoteWord.objects
            .filter(
                noun=noun,
                note__user=user,
                note__created_at__year=dt.year,
                note__created_at__month=dt.month,
            )
            .values_list("note_id", flat=True)
        )

        return (
            Notes.objects
            .filter(id__in=note_ids)
            .order_by("created_at")       # 최신순
            .select_related("emotion")     # 필요하다면
        )