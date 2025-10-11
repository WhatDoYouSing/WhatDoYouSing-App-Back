from django.urls import path
from .views import *

app_name = 'notes'

urlpatterns = [
    path('detail/<int:note_id>/', NoteDetailView.as_view()),
    path("emotion/<int:note_id>/<str:emotion_name>/", NoteEmotionToggleView.as_view(), name="note-emotion-toggle"),
    path("sameuser/<int:user_id>/",SameUserContentsView.as_view()),
    path("samesongnote/<int:note_id>/",SameSongNoteView.as_view()),
    path("samesongpli/<int:note_id>/",SameSongPliView.as_view()),
    path("comments/<int:note_id>/",NoteCommentView.as_view()),
    path("comments/list/<int:note_id>/",NoteCommentListView.as_view()),
    path("comments/delete/<int:comment_id>/", NoteCommentEditDeleteView.as_view()),
    path("comments/edit/<int:comment_id>/", NoteCommentEditDeleteView.as_view()),
    path("reply/delete/<int:reply_id>/", NoteReplyEditDeleteView.as_view()),
    path("reply/edit/<int:reply_id>/", NoteReplyEditDeleteView.as_view()),
    path("comments/report/<str:content_type>/<str:comment_type>/<int:content_id>/", ReportCommentView.as_view()),
    path("comments/like/<int:content_id>/", ToggleLikeView.as_view()),

]
