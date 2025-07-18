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
            # 태그 개수 카운팅
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


# 노트 수정
class NoteUpdateView(views.APIView):
    def put(self, request, pk, format=None):
        note = get_object_or_404(Notes, pk=pk)
        old_emotion = note.emotion
        old_tag_time = list(note.tag_time.all())
        old_tag_season = list(note.tag_season.all())
        old_tag_context = list(note.tag_context.all())

        if request.user == note.user:
            serializer = YT_NotesUploadSerializer(
                note, data=request.data
            )  # 얘만 link 필드까지 있음
            if serializer.is_valid():
                updated_note = (
                    serializer.save()
                )  # article에 user 정보 있기 때문에 (user=request.user) 생략

                if old_emotion:
                    old_emotion.count = max(old_emotion.count - 1, 0)
                    old_emotion.save()

                # ✅ 기존 태그들 -1
                for tag in old_tag_time:
                    tag.count = max(tag.count - 1, 0)
                    tag.save()
                for tag in old_tag_season:
                    tag.count = max(tag.count - 1, 0)
                    tag.save()
                for tag in old_tag_context:
                    tag.count = max(tag.count - 1, 0)
                    tag.save()

                # ✅ 새로운 emotion +1
                if updated_note.emotion:
                    updated_note.emotion.count += 1
                    updated_note.emotion.save()

                # ✅ 새로운 태그들 +1
                for tag in updated_note.tag_time.all():
                    tag.count += 1
                    tag.save()
                for tag in updated_note.tag_season.all():
                    tag.count += 1
                    tag.save()
                for tag in updated_note.tag_context.all():
                    tag.count += 1
                    tag.save()
                return Response(
                    {"message": "노트 수정 성공", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )


# 노트 삭제
class NoteDelView(views.APIView):
    def delete(self, request, pk, format=None):
        note = get_object_or_404(Notes, pk=pk)
        if request.user == note.user:
            note.delete()
            return Response(
                {"message": "노트 삭제 성공"}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
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


# 플리 삭제
class PliDelView(views.APIView):
    def delete(self, request, pk, format=None):
        pli = get_object_or_404(Plis, pk=pk)
        if request.user == pli.user:
            pli.delete()
            return Response(
                {"message": "플리 삭제 성공"}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )
