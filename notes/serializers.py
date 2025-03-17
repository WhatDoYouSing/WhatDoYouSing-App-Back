from rest_framework import serializers
from .models import NoteComment, NoteReply

class NoteReplySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = NoteReply
        fields = ["id", "user", "created_at", "content", "likes_count"]

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "nickname": obj.user.nickname,
            "profile": obj.user.profile
        }

    def get_likes_count(self, obj):
        return obj.likes.count()


class NoteCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    replies = NoteReplySerializer(many=True, read_only=True)  # ✅ 대댓글 포함
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = NoteComment
        fields = ["id", "user", "created_at", "content", "reply_count", "replies", "likes_count"]

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "nickname": obj.user.nickname,
            "profile": obj.user.profile
        }

    def get_reply_count(self, obj):
        return obj.replies.count()  # 대댓글 개수 반환

    def get_likes_count(self, obj):
        return obj.likes.count()
