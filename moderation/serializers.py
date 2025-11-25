from rest_framework import serializers

class BlockActionSerializer(serializers.Serializer):
    BLOCK_CHOICES = [
        "user",
        "note",
        "pli",
        "note_comment",
        "note_reply",
        "pli_comment",
        "pli_reply",
    ]
    target_type = serializers.ChoiceField(choices=BLOCK_CHOICES)
    target_id = serializers.IntegerField(min_value=1)
