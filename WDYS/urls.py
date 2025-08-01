"""
URL configuration for WDYS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    path('admin/', admin.site.urls),
    #path('',include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('collects/', include('collects.urls')),
    path('home/', include('home.urls')),
    path('mypage/', include('mypage.urls')),
    path('notes/', include('notes.urls')),
    path('notifs/', include('notifs.urls')),
    path('playlists/', include('playlists.urls')),
    path('records/', include('records.urls')),
    path('search/', include('search.urls')),
    path('settings/', include('settings.urls')),
    path('social/', include('social.urls')),
    path('uploads/', include('uploads.urls')),
]