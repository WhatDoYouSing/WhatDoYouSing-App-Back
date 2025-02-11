from rest_framework import serializers
from notes.models import *
from accounts.models import *
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta


class FunctionMixin:

    def get_author_nickname(self, obj):
        return obj.author.nickname

    def get_author_profile(self, obj):
        return obj.author.profile

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comment.count()

    def get_recomments_count(self, obj):
        return obj.recomments.count()

    def get_com_count(self, obj):
        comment_count = obj.comment_count()
        recomment_count = obj.recomment_count()

        return comment_count + recomment_count

    def get_com_likes_count(self, obj):
        return obj.com_likes.count()

    def get_com_relikes_count(self, obj):
        return obj.com_relikes.count()

    def get_is_scraped(self, obj):
        request_user = self.context["request"].user
        return request_user in obj.scrap.all()


# 노트 업로드(음원)
class NotesUploadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notes
        fields = [
            "id",
            "user",
            "album_art",
            "song_title",
            "artist",
            "lyrics",
            "location_name",
            "location_address",
            "emotion",
            "memo",
            "visibility",
            "tag_time",
            "tag_season",
            "tag_context",
            "created_at",
        ]
