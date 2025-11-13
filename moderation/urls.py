from django.urls import path
from .views import *

app_name = "moderation"

urlpatterns = [
    path("blocking/", BlockingView.as_view(), name="blocking"),
]
