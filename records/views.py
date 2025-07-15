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