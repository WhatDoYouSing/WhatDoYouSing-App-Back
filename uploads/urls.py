from django.urls import path
from .views import *

app_name = "uploads"

urlpatterns = [
    path("note/", SongNoteUploadView.as_view()),  # 노트(음원)업로드
    path("note/yt/", YTNoteUploadView.as_view()),  # 노트(유튜브)업로드
    path("note/self/", NoteUploadView.as_view()),  # 노트(직접)업로드
    path("note/update/<int:pk>/", NoteUpdateView.as_view()),  # 노트 수정
    path("note/del/<int:pk>/", NoteDelView.as_view()),  # 노트 삭제
    # path("pli/scrap/<int:scrap_list_id>/", ScrapNotesForPlisView.as_view()),  # 플리 생성 시 보관함 목록
    path("pli/notelist/", NoteListView.as_view()),  # 플리 생성 시 노트 목록
    path("pli/", PliUploadView.as_view()),  # 플리 업로드
    path("pli/update/<int:pk>/", PliUpdateView.as_view()),  # 플리 수정
    path("pli/del/<int:pk>/", PliDelView.as_view()),  # 노트 삭제
    path(
        "report/user/<str:post_type>/<int:post_id>/",
        UserReportView.as_view(),
        name="user-report",
    ),  # 게시글 작성자 신고
    path(
        "report/<str:report_type>/<int:content_id>/", PostReportView.as_view()
    ),  # 게시글 신고
    # 게시글 차단/해제
    # path("notes/block/<int:pk>/", BlockNoteView.as_view(), name="note-block"),
    # path("plis/block/<int:pk>/", BlockPliView.as_view(), name="pli-block"),
    # 작성자 차단/해제
    # path("author-block/<int:user_id>/", BlockAuthorView.as_view(), name="author-block"),
    path("spotify/callback/", SpotifyAcessTokenView.as_view())
]
