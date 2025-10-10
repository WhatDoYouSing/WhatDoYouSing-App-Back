from django.urls import path
from .views import *

app_name = 'playlists'

urlpatterns = [
    
    path('detail/<int:pk>/',PlaylistDetailView.as_view()),
    path('sameuser/<int:user_id>/', SameUserPliView.as_view()),
    path('comments/<int:pli_id>/', PliCommentView.as_view()),
    path('comments/list/<int:pli_id>/', PliCommentListView.as_view()),
    path('comments/delete/<int:comment_id>/', PliCommentEditDeleteView.as_view()),
    path('comments/edit/<int:comment_id>/', PliCommentEditDeleteView.as_view()),
    path('reply/delete/<int:reply_id>/', PliReplyEditDeleteView.as_view()),
    path('reply/edit/<int:reply_id>/', PliReplyEditDeleteView.as_view()),


]