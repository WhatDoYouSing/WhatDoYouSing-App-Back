from django.urls import path
from .views import *

urlpatterns = [
    path('main/', MainRecordView.as_view()),
    path('emotions/', EmotionsRecordView.as_view()),
    #path("words/", WordTopView.as_view(), name="word-top"),
    #path("words/<str:word>/", WordDetailView.as_view(), name="word-detail"),
]