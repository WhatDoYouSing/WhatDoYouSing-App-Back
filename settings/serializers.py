from rest_framework import serializers
from .models import Notice, FAQ

class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ["id", "title", "manager_profile", "manager_name", "content", "created_at"]

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "created_at"]
