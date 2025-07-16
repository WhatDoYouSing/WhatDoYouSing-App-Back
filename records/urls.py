from django.urls import path
from .views import *

urlpatterns = [
    path('main/', MainRecordView.as_view()),
    path('emotions/', EmotionsRecordView.as_view()),
]