from django.utils import timezone
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, Activity, Device
from .serializers import NotificationSerializer, ActivitySerializer, DeviceSerializer


class NotificationListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        qs = Notification.objects.filter(user=request.user)
        data = NotificationSerializer(qs, many=True).data
        return Response(data)


class NotificationMarkReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        ids = request.data.get("ids", [])
        updated = Notification.objects.filter(
            user=request.user, id__in=ids, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"marked": updated})


class ActivityListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        qs = Activity.objects.filter(user=request.user)
        data = ActivitySerializer(qs, many=True).data
        return Response(data)


class DeviceRegisterView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["expo_token"]

        Device.objects.update_or_create(
            user=request.user, defaults={"expo_token": token}
        )
        return Response(
            {"message": "Expo 토큰 등록 완료"}, status=status.HTTP_201_CREATED
        )
