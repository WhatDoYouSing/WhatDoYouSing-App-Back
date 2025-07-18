from django.urls import path
from .views import *

app_name = "search"

urlpatterns = [
    path("result/", SearchView.as_view()),  # 탐색 결과(통합)
    path("resultnote/", SearchNotesView.as_view()),  # 탐색 결과(노트)
    path("resultpli/", SearchPlisView.as_view()),  # 탐색 결과(플리)
    path("resultwriter/", SearchWritersView.as_view()),  # 탐색 결과(작성자)
]
