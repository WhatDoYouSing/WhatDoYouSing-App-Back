from django.urls import path
from .views import *

app_name = 'collects'

urlpatterns = [
    path('post/<str:type>/<int:scrap_list_id>/<int:content_id>/', CollectView.as_view()),
    path('list/', ScrapListView.as_view()),
]
