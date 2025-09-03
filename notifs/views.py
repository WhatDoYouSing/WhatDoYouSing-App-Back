from django.utils import timezone
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType

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
        qs = (
            Notification.objects.filter(user=request.user)
            .select_related("actor")
            .order_by("-created_at")
        )
        # actor 기준으로 필터
        # 2) 차단한 사용자 알림만 제외 (actor가 없는 시스템 알림은 유지)
        blocked = set(blocked_user_ids(request.user))

        if blocked:
            qs = qs.exclude(actor_id__in=blocked)

        # 3) target_map 미리 구성해서 GenericFK N+1 제거
        ct_obj_ids = {}
        for n in qs:
            if n.ct_id and n.obj_id:
                ct_obj_ids.setdefault(n.ct_id, set()).add(n.obj_id)

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

                # Notes/Plis는 작성자도 필요하므로 select_related("user")
                if model is Notes:
                    objs = Notes.objects.filter(id__in=obj_ids).select_related("user")
                elif model is Plis:
                    objs = Plis.objects.filter(id__in=obj_ids).select_related("user")
                else:
                    objs = model.objects.filter(id__in=obj_ids)

                for o in objs:
                    target_map[(ct_id, o.id)] = o

        serializer = NotificationSerializer(
            qs, many=True, context={"target_map": target_map}
        )
        return Response(serializer.data)


class NotificationMarkReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        ids = request.data.get("ids", [])
        updated = Notification.objects.filter(
            user=request.user, id__in=ids, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"marked": updated})


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
            expo_token=token, defaults={"user": request.user}
        )
        return Response(
            {"message": "Expo 토큰 등록 완료"}, status=status.HTTP_201_CREATED
        )
