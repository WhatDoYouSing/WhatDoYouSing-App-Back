from django.urls import path
from .views import *

app_name = "uploads"

urlpatterns = [
    path("note/", SongNoteUploadView.as_view()),  # 노트(음원)업로드
    path("note/yt/", YTNoteUploadView.as_view()),  # 노트(유튜브)업로드
    path("note/self/", NoteUploadView.as_view()),  # 노트(직접)업로드
    path("pli/notelist/", NoteListView.as_view()),  # 플리 생성 시 노트 목록
    path("pli/", PliUploadView.as_view()),
]
