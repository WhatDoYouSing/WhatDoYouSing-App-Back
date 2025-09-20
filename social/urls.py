from django.urls import path
from .views import *
app_name = 'social'

urlpatterns = [
    path('follower/',FollowerListView.as_view()),
    path('following/',FollowingListView.as_view()),
    path("follow/<int:user_id>/", FollowToggleView.as_view()),
    path('follower/others/', OthersFollowerListView.as_view()),
    path('following/others/', OthersFollowingListView.as_view()),
]