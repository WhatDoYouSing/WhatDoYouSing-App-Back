from django.urls import path
from .views import *
app_name = 'home'
urlpatterns = [
    path('', HomeView.as_view()),
    path('pli/', HomePliView.as_view()),
    path('note/', HomeNoteView.as_view()),
    path('follow/', HomeFollowView.as_view()),
    path('follow/pli/', HomeFollowPliView.as_view()),
    path('follow/note/', HomeFollowNoteView.as_view()),

]