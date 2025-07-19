from django.urls import path
from .views import *

urlpatterns = [
    path("notice/", NoticeListView.as_view()),  
    path("notice/<int:pk>/", NoticeDetailView.as_view()), 
    path("faq/", FAQListView.as_view()),
    path("faq/<int:pk>/", FAQDetailView.as_view()),
    path("change/push/", PushChangeView.as_view()),
    path("change/marketing/", MarketingChangeView.as_view()),
]