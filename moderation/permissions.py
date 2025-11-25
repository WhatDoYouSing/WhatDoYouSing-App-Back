# moderation/permissions.py
from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound

from moderation.utils.blocking import (
    is_note_blocked,
    is_pli_blocked,
    blocked_user_ids,
)
from notes.models import Notes, Plis


class IsNotBlocked(BasePermission):
    message = "Not found."

    def has_object_permission(
        self,
        request,
        view,
        obj: Any,
    ) -> bool:
        user = request.user
        if not user.is_authenticated:
            return True

        # ① 노트 / ② 플리 차단 검사 (작성자 차단 포함)
        if isinstance(obj, Notes) and is_note_blocked(user, obj):
            raise NotFound()
        if isinstance(obj, Plis) and is_pli_blocked(user, obj):
            raise NotFound()

        # ③ 그 외 객체라도 user_id 속성이 있으면 작성자 차단 검사
        if hasattr(obj, "user_id") and obj.user_id in blocked_user_ids(user):
            raise NotFound()

        return True
