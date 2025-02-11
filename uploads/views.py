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
        serializer = NotesUploadSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(user=request.user)
            # 태그 개수 카운팅팅
            if note.emotion:
                note.emotion.count += 1
                note.emotion.save()
            if note.tag_time:
                note.tag_time.count += 1
                note.tag_time.save()
            if note.tag_season:
                note.tag_season.count += 1
                note.tag_season.save()
            if note.tag_context:
                note.tag_context.count += 1
                note.tag_context.save()
            return Response(
                {"message": "노트(음원) 작성 성공", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "노트(음원) 작성 실패", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


"""
# 노트 업로드(유튜브)
class YTNoteUploadView(views.APIView):
    serializer_class = 

# 노트 업로드(직접)
class NoteUploadView(views.APIView):
    serializer_class = 

class PostAddView(views.APIView):
    serializer_class = PostSerializer
    #permission_classes = [IsAuthenticated]  

    def post(self, request, format=None):  # 게시글 작성 POST 메소드
        if not request.user.is_authenticated:  # Check if the user is not authenticated
            return Response({"message": "로그인을 해주세요"}, status=status.HTTP_401_UNAUTHORIZED)
        
        required_fields = ['lyrics', 'content', 'title', 'singer', 'sings_emotion']
        for field in required_fields:
            if field not in request.data:
                return Response({"message": f"{field} 필드를 작성해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response({"message": "가사 작성 성공", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "가사 작성 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class PostDelView(views.APIView):
    serializer_class = PostSerializer

    def delete(self, request, pk, format=None):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return Response({"message": "가사 삭제 성공"}, status=status.HTTP_204_NO_CONTENT)
        

        """
