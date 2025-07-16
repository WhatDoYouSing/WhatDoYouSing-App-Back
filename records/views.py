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
# views.py
from collections import OrderedDict
from datetime import datetime
from django.db.models import Count
from rest_framework import status, views
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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