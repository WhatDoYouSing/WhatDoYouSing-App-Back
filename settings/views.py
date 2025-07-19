from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Notice, FAQ
from .serializers import NoticeSerializer, FAQSerializer
from accounts.models import User
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404

# 공지사항 목록 조회
class NoticeListView(ListAPIView):
    queryset = Notice.objects.all().order_by("-created_at")  # 최신순 정렬
    serializer_class = NoticeSerializer

# 공지사항 상세 조회
class NoticeDetailView(RetrieveAPIView):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    lookup_field = "pk"  # URL에서 `id` 값을 가져와서 조회

# FAQ 목록 조회
class FAQListView(ListAPIView):
    queryset = FAQ.objects.all().order_by("-created_at")  # 최신순 정렬
    serializer_class = FAQSerializer

# FAQ 상세 조회
class FAQDetailView(RetrieveAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    lookup_field = "pk"  # URL에서 `id` 값을 가져와서 조회


class PushChangeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "consent": user.push_notification_consent
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user

        user.push_notification_consent = not user.push_notification_consent
        user.save()

        if user.push_notification_consent:
            message = f"{user.nickname}님, 서비스 푸시 알림 동의 상태를 '동의'로 변경했습니다."
        else:
            message = f"{user.nickname}님, 서비스 푸시 알림 동의 상태를 '취소'로 변경했습니다."

        return Response({"message": message}, status=status.HTTP_200_OK)
    
class MarketingChangeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "consent": user.marketing_consent
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user

        user.marketing_consent = not user.marketing_consent
        user.save()

        if user.marketing_consent:
            message = f"{user.nickname}님, 광고성 정보 수신 동의 상태를 '동의'로 변경했습니다."
        else:
            message = f"{user.nickname}님, 광고성 정보 수신 동의 상태를 '취소'로 변경했습니다."

        return Response({"message": message}, status=status.HTTP_200_OK)