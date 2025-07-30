from django.urls import path
from .views import *

app_name = "moderation"

urlpatterns = [
    # # 게시글 차단/해제
    # path("notes/block/<int:pk>/", BlockNoteView.as_view(), name="note-block"),
    # path("plis/block/<int:pk>/", BlockPliView.as_view(), name="pli-block"),
    # # 작성자 차단/해제
    # path("author-block/<int:user_id>/", BlockAuthorView.as_view(), name="author-block"),
    path("blocking/", BlockingView.as_view(), name="blocking"),
]
