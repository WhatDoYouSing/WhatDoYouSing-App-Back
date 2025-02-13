from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Notice, FAQ
from .serializers import NoticeSerializer, FAQSerializer

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
