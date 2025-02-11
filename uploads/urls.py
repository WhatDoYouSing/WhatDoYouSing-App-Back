from django.urls import path
from .views import *

app_name = "uploads"

urlpatterns = [
    path("note/songs/", SongNoteUploadView.as_view()),
    #path("note/yt/", YTNoteUploadView.as_view()),
    #path("note/self/", NoteUploadView.as_view())
    #path("pli/", PliUploadView.as_view())
]