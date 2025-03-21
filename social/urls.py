from django.urls import path
from .views import *
app_name = 'social'

urlpatterns = [
    path('follower/',FollowerListView.as_view()),
    path('following/',FollowingListView.as_view()),
    path("follow/<int:user_id>/", FollowToggleView.as_view()),
]