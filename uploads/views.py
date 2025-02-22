from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.permissions import *
from rest_framework import status, permissions

# from .permissions import *
from rest_framework import views
from rest_framework.status import *
from rest_framework.response import Response
from django.db.models import Q, Count
from django.conf import settings

# import requests
# import datetime

from .serializers import *
from notes.models import *


# 노트 업로드(음원)
class SongNoteUploadView(views.APIView):
    def post(self, request):
        serializer = Song_NotesUploadSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(user=request.user)
            # 태그 개수 카운팅팅
            if note.emotion:
                note.emotion.count += 1
                note.emotion.save()

            for tag in note.tag_time.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_season.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_context.all():
                tag.count += 1
                tag.save()

            return Response(
                {"message": "노트(음원) 작성 성공", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "노트(음원) 작성 실패", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 노트 업로드(유튜브)
class YTNoteUploadView(views.APIView):
    def post(self, request):
        serializer = YT_NotesUploadSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(user=request.user)
            # 태그 개수 카운팅팅
            if note.emotion:
                note.emotion.count += 1
                note.emotion.save()

            for tag in note.tag_time.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_season.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_context.all():
                tag.count += 1
                tag.save()

            return Response(
                {"message": "노트(유튜브) 작성 성공", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "노트(유튜브) 작성 실패", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 노트 업로드(직접)
class NoteUploadView(views.APIView):
    def post(self, request):
        serializer = NotesUploadSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(user=request.user)
            # 태그 개수 카운팅팅
            if note.emotion:
                note.emotion.count += 1
                note.emotion.save()

            for tag in note.tag_time.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_season.all():
                tag.count += 1
                tag.save()

            for tag in note.tag_context.all():
                tag.count += 1
                tag.save()

            return Response(
                {"message": "노트(직접) 작성 성공", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "노트(직접) 작성 실패", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 플리 생성 시 노트 목록
class NoteListView(views.APIView):
    def get(self, request, format=None):

        keyword = request.GET.get("keyword")

        myposts = Notes.objects.filter(user=request.user).order_by("-created_at")

        if keyword:
            myposts = myposts.filter(
                Q(lyrics__icontains=keyword)
                | Q(artist__icontains=keyword)
                | Q(song_title__icontains=keyword)
            )

        serializer = NotesListSerializer(myposts, many=True)
        return Response(
            {"message": "MY 노트 목록 반환 성공", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class PliUploadView(views.APIView):
    def post(self, request, format=None):
        serializer = PliUploadSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            plis = serializer.save()  # serializers.py의 create() 메서드 호출

            for tag in plis.tag_time.all():
                tag.count += 1
                tag.save()

            for tag in plis.tag_season.all():
                tag.count += 1
                tag.save()

            for tag in plis.tag_context.all():
                tag.count += 1
                tag.save()

            return Response(
                {"message": "플리 업로드 성공", "data": PliUploadSerializer(plis).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
