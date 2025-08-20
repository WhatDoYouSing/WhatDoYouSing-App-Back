from django.utils import timezone
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, Activity, Device
from .serializers import NotificationSerializer, ActivitySerializer, DeviceSerializer

from moderation.mixins import BlockFilterMixin
from moderation.models import UserBlock, NoteBlock, PliBlock
from accounts.models import User
from moderation.utils.blocking import blocked_user_ids
from notes.models import Notes, Plis


class NotificationListView(BlockFilterMixin, views.APIView):
    permission_classes = [IsAuthenticated]
    block_model = User

    def get(self, request, format=None):
        qs = Notification.objects.filter(user=request.user)
        # actor 기준으로 필터
        qs = self.filter_blocked(qs.filter(actor__isnull=False))

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


from django.contrib.contenttypes.models import ContentType


class ActivityListView(BlockFilterMixin, views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """qs = Activity.objects.filter(user=request.user)
        data = ActivitySerializer(qs, many=True).data
        return Response(data)"""
        user = request.user
        qs = Activity.objects.filter(user=user)

        # target 모델 중 user 필드가 있는 경우에만 필터링
        blocked_users = set(blocked_user_ids(user))
        filtered_qs = []
        for act in qs:
            target = act.target
            owner = getattr(target, "user", None)
            if not owner or owner.id not in blocked_users:
                filtered_qs.append(act)
        # --- bulk로 target들 미리 조회해서 매핑 만들기 (ContentType, obj_id 기반) ---
        # ct_id -> set(obj_ids)
        ct_obj_ids = {}
        for act in filtered_qs:
            if act.ct_id and act.obj_id:
                ct_obj_ids.setdefault(act.ct_id, set()).add(act.obj_id)

        target_map = {}
        if ct_obj_ids:
            for ct_id, obj_ids in ct_obj_ids.items():
                try:
                    ct = ContentType.objects.get_for_id(ct_id)
                except ContentType.DoesNotExist:
                    continue
                model = ct.model_class()
                if model is None:
                    continue

                # 모델별로 bulk 조회 (Notes, Plis 최적화)
                if model == Notes:
                    objs = Notes.objects.filter(id__in=obj_ids).select_related("user")
                elif model == Plis:
                    objs = Plis.objects.filter(id__in=obj_ids).select_related("user")
                else:
                    objs = model.objects.filter(id__in=obj_ids).select_related("user")

                for o in objs:
                    target_map[(ct_id, o.id)] = o

        serializer = ActivitySerializer(
            filtered_qs, many=True, context={"target_map": target_map}
        )

        return Response(serializer.data)


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
