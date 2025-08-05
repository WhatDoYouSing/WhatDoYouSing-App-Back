# import random
# from rest_framework import serializers
# from notes.models import *
# from .models import *
# from accounts.models import *
# from accounts.serializers import UserSerializer
# from datetime import datetime, timedelta


# # ────────────────────────────────────────────────────────────────────────────
# # 게시글 차단 (노트)
# # ────────────────────────────────────────────────────────────────────────────
# class NoteBlockSerializer(serializers.ModelSerializer):
#     note_id = serializers.PrimaryKeyRelatedField(
#         queryset=Notes.objects.all(), source="note", write_only=True
#     )

#     class Meta:
#         model = NoteBlock
#         fields = ["note_id"]

#     def create(self, validated_data):
#         user = self.context["request"].user
#         note = validated_data["note"]
#         obj, _ = NoteBlock.objects.get_or_create(user=user, note=note)
#         return obj


# # ────────────────────────────────────────────────────────────────────────────
# # 게시글 차단 (플리)
# # ────────────────────────────────────────────────────────────────────────────
# class PliBlockSerializer(serializers.ModelSerializer):
#     pli_id = serializers.PrimaryKeyRelatedField(
#         queryset=Plis.objects.all(), source="pli", write_only=True
#     )

#     class Meta:
#         model = PliBlock
#         fields = ["pli_id"]

#     def create(self, validated_data):
#         user = self.context["request"].user
#         pli = validated_data["pli"]
#         obj, _ = PliBlock.objects.get_or_create(user=user, pli=pli)
#         return obj


# # ────────────────────────────────────────────────────────────────────────────
# # 게시글 **작성자** 차단
# # ────────────────────────────────────────────────────────────────────────────
# class AuthorBlockSerializer(serializers.ModelSerializer):
#     # 차단 대상(작성자)만 보내면 되므로 PK 필드 하나만 받음
#     blocked_user_id = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(), source="blocked_user", write_only=True
#     )

#     class Meta:
#         model = UserBlock
#         fields = ["blocked_user_id"]

#     def validate_blocked_user(self, user):
#         if self.context["request"].user == user:
#             raise serializers.ValidationError("자기 자신은 차단할 수 없습니다.")
#         return user

#     def create(self, validated_data):
#         user = self.context["request"].user
#         blocked_user = validated_data["blocked_user"]
#         obj, _ = UserBlock.objects.get_or_create(user=user, blocked_user=blocked_user)
#         return obj

from rest_framework import serializers


class BlockActionSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=["user", "note", "pli"])
    target_id = serializers.IntegerField(min_value=1)
