# uploads/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotFound
from notes.utils.blocking import is_note_blocked, is_pli_blocked
from notes.models import Notes, Plis


class IsNotBlockedNote(BasePermission):
    """노트 또는 작성자가 차단돼 있으면 404 반환"""

    message = "Not found."  # 차단 여부를 노출하지 않도록 404 처리

    def has_object_permission(self, request, view, obj):
        if is_note_blocked(request.user, obj):
            raise NotFound(self.message)
        return True


class IsNotBlockedPli(BasePermission):
    message = "Not found."

    def has_object_permission(self, request, view, obj):
        if is_pli_blocked(request.user, obj):
            raise NotFound(self.message)
        return True
