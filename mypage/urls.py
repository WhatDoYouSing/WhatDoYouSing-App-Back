from django.urls import path
from .views import *

urlpatterns = [
    path('profile/', MyPageView.as_view()),
    path('contents/', MyContentView.as_view()),
    path('titles/', TitleListView.as_view()),
    path('update/title/', TitleChoiceView.as_view()),
    path('update/profile/', ProfileChoiceView.as_view()),
    path('update/nickname/', NicknameUpdateView.as_view()),
    #path('calendar/', MyCalendarView.as_view()),
    path('others/profile/', OthersPageView.as_view()),
    path('others/contents/', OthersContentView.as_view()),
]