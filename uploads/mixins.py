# uploads/mixins.py
from notes.models import NoteBlock, PliBlock, UserBlock


class BlockFilterMixin:
    """get_queryset에서 차단된 글·작성자를 자동 제외"""

    block_model = None  # NoteBlock 또는 PliBlock
    content_model = None  # Notes 또는 Plis
    content_fk_name = ""  # 'note' 또는 'pli'

    def filter_blocked(self, qs):
        user = self.request.user
        if not user.is_authenticated:
            return qs

        # ① 게시글 차단
        blocked_ids = self.block_model.objects.filter(user=user).values_list(
            f"{self.content_fk_name}_id", flat=True
        )

        # ② 작성자 차단
        blocked_users = UserBlock.objects.filter(user=user).values_list(
            "blocked_user_id", flat=True
        )

        return qs.exclude(id__in=blocked_ids).exclude(user_id__in=blocked_users)

    def get_queryset(self):
        qs = super().get_queryset()
        return self.filter_blocked(qs)
