from django.urls import path
from .views import *

app_name = 'collects'

urlpatterns = [
    path('post/<str:type>/<int:scrap_list_id>/<int:content_id>/', CollectView.as_view()),
    path('list/', ScrapListView.as_view()),
    path('listcheck/<str:type>/<int:content_id>/', ScrapListCheckView.as_view()),
    path('detail/<int:scrap_list_id>/',ScrapListDetailView.as_view()),
    path('new/', ScrapListCreateView.as_view()),
    path('edit/<int:scrap_list_id>/',ScrapListEditView.as_view()),
    path("delete/<int:content_id>/", ScrapListDeleteView.as_view()),
]
