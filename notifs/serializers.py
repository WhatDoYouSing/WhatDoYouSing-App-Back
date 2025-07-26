from rest_framework import serializers
from .models import Notification, Activity, Device


class NotificationSerializer(serializers.ModelSerializer):
    actor_nickname = serializers.CharField(source="actor.nickname", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor_nickname",
            "notif_type",
            "content",
            "is_read",
            "created_at",
        ]


# class ActivitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Activity
#         fields = ["id", "activity_type", "created_at"]
class ActivitySerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    parent_text = serializers.SerializerMethodField()
    target_text = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "activity_type",
            "created_at",
            "text",
            "parent_text",
            "target_text",
        ]

    # ↓↓↓ helper ↓↓↓
    def _comment_snippet(self, obj, max_len=120):
        return (
            (obj.content[:max_len] + "…") if len(obj.content) > max_len else obj.content
        )

    def get_text(self, act):
        if act.activity_type in ["comment_note", "comment_pli"]:
            return self._comment_snippet(act.target)
        if act.activity_type in ["reply_note", "reply_pli"]:
            return self._comment_snippet(act.target)
        return None

    def get_parent_text(self, act):
        if act.activity_type in ["reply_note", "reply_pli"]:
            return self._comment_snippet(act.target.comment)
        return None

    def get_target_text(self, act):
        if act.activity_type in ["like_comment", "like_reply"]:
            return self._comment_snippet(act.target)
        return None


class DeviceSerializer(serializers.ModelSerializer):
    expo_token = serializers.CharField(max_length=255)

    class Meta:
        model = Device
        fields = ["expo_token"]
