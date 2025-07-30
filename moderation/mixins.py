from moderation.utils.blocking import blocked_item_ids, blocked_user_ids


class BlockFilterMixin:
    """
    목록/검색 뷰에서 차단 글·작성자를 자동 제외.

    사용법:
        class SearchNotesView(BlockFilterMixin, ListAPIView):
            block_model = Notes   # 또는 Plis
    """

    block_model = None  # 반드시 Notes 또는 Plis 로 지정

    def filter_blocked(self, qs):
        u = self.request.user
        if not u.is_authenticated or self.block_model is None:
            return qs

        qs = qs.exclude(id__in=blocked_item_ids(u, self.block_model))
        qs = qs.exclude(user_id__in=blocked_user_ids(u))
        return qs

    def get_queryset(self):
        return self.filter_blocked(super().get_queryset())
