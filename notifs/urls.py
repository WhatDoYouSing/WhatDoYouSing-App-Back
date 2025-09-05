from django.urls import path
from .views import *

app_name = "notifs"

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/markread/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
    path("activities/", ActivityListView.as_view(), name="activity-list"),
    path(
        "activities/markread/",
        ActivityMarkReadView.as_view(),
        name="activity-mark-read",
    ),
    path("devices/", DeviceRegisterView.as_view(), name="device-register"),
]
