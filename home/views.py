from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notes.models import *
from accounts.models import User
from playlists.models import *
from .serializers import *
from social.models import *
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from notifs.models import *
from moderation.mixins import BlockFilterMixin
from moderation.models import UserBlock, NoteBlock, PliBlock


from rest_framework.pagination import PageNumberPagination


class TenItemPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class HomeView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # 현재 로그인된 유저

        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        # Notes 필터링: 공개 노트 + 친구의 'friends' 공개 노트 + 자신이 작성한 노트
        notes = Notes.objects.filter(
            Q(visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 노트
            | Q(user=user)  # 자신이 작성한 노트
        ).order_by("-created_at")

        self.block_model = Notes
        notes = self.filter_blocked(notes)

        # Plis 필터링: 공개 플리 + 친구의 'friends' 공개 플리 + 자신이 작성한 플리
        plis = Plis.objects.filter(
            Q(visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 플리
            | Q(user=user)  # 자신이 작성한 플리
        ).order_by("-created_at")

        self.block_model = Plis
        plis = self.filter_blocked(plis)

        self.block_model = None  # 사이드이펙트 방지

        # 데이터 통합
        note_data = [NoteSerializer(n).data for n in notes]
        pli_data = [PliSerializer(p).data for p in plis]
        combined = sorted(
            note_data + pli_data, key=lambda x: x["created_at"], reverse=True
        )

        # 페이지네이션 적용
        paginator = TenItemPagination()
        paginated_data = paginator.paginate_queryset(combined, request)

        # combined_data = []
        # for note in notes:
        #     combined_data.append(NoteSerializer(note).data)
        # for pli in plis:
        #     combined_data.append(PliSerializer(pli).data)

        # 최신순으로 정렬
        # combined_data.sort(key=lambda x: x['created_at'], reverse=True)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "통합 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": paginated_data},
            },
            status=status.HTTP_200_OK,
        )


class HomePliView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 임시 - 필요 시 페이지네이션 추가

        user = request.user
        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        plis = Plis.objects.filter(
            Q(visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 플리
            | Q(user=user)  # 자신이 작성한 플리
        ).order_by("-created_at")

        self.block_model = Plis
        plis = self.filter_blocked(plis)
        self.block_model = None

        paginator = TenItemPagination()
        paginated_plis = paginator.paginate_queryset(plis, request)
        serializers = PliSerializer(paginated_plis, many=True)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "플리 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": serializers.data},
            },
            status=status.HTTP_200_OK,
        )


class HomeNoteView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 임시 - 필요 시 페이지네이션 추가

        user = request.user
        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        notes = Notes.objects.filter(
            Q(visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 노트
            | Q(user=user)  # 자신이 작성한 노트
        ).order_by("-created_at")

        self.block_model = Notes
        notes = self.filter_blocked(notes)
        self.block_model = None

        paginator = TenItemPagination()
        paginated_notes = paginator.paginate_queryset(notes, request)
        serializers = NoteSerializer(paginated_notes, many=True)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "노트 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": serializers.data},
            },
            status=status.HTTP_200_OK,
        )


class HomeFollowView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 임시 - 필요 시 페이지네이션 추가

        user = request.user  # 현재 로그인된 유저

        following_users = UserFollows.objects.filter(follower=user).values("following")

        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        # Notes 필터링: 팔로우한 사람의 'public' 노트 + 친구의 'friends' 공개 노트 + 자신이 작성한 노트
        notes = Notes.objects.filter(
            Q(user__in=following_users, visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 노트
            | Q(user=user)  # 자신이 작성한 노트
        ).order_by("-created_at")

        # Plis 필터링: 공개 플리 + 친구의 'friends' 공개 플리 + 자신이 작성한 플리
        plis = Plis.objects.filter(
            Q(user__in=following_users, visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 플리
            | Q(user=user)  # 자신이 작성한 플리
        ).order_by("-created_at")

        self.block_model = Notes
        notes = self.filter_blocked(notes)
        self.block_model = Plis
        plis = self.filter_blocked(plis)
        self.block_model = None

        # 데이터 통합
        combined_data = []
        for note in notes:
            combined_data.append(NoteSerializer(note).data)
        for pli in plis:
            combined_data.append(PliSerializer(pli).data)

        # 최신순으로 정렬
        combined_data.sort(key=lambda x: x["created_at"], reverse=True)

        paginator = TenItemPagination()
        paginated_data = paginator.paginate_queryset(combined_data, request)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "팔로우 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": paginated_data},
            },
            status=status.HTTP_200_OK,
        )


class HomeFollowPliView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 임시 - 필요 시 페이지네이션 추가

        user = request.user
        following_users = UserFollows.objects.filter(follower=user).values("following")

        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        plis = Plis.objects.filter(
            Q(user__in=following_users, visibility="public")
            | Q(user__in=friends, visibility="friends")
            | Q(user=user)
        ).order_by("-created_at")

        self.block_model = Plis
        plis = self.filter_blocked(plis)
        self.block_model = None

        paginator = TenItemPagination()
        paginated_plis = paginator.paginate_queryset(plis, request)
        serializers = PliSerializer(paginated_plis, many=True)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "팔로우 플리 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": serializers.data},
            },
            status=status.HTTP_200_OK,
        )


class HomeFollowNoteView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 임시 - 필요 시 페이지네이션 추가

        user = request.user
        following_users = UserFollows.objects.filter(follower=user).values("following")

        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values(
                    "follower"
                )
            )
        ).values("following")

        # Notes 필터링: 팔로우한 사람의 'public' 노트 + 친구의 'friends' 공개 노트 + 자신이 작성한 노트
        notes = Notes.objects.filter(
            Q(user__in=following_users, visibility="public")
            | Q(user__in=friends, visibility="friends")  # 친구가 작성한 노트
            | Q(user=user)  # 자신이 작성한 노트
        ).order_by("-created_at")

        self.block_model = Notes
        notes = self.filter_blocked(notes)
        self.block_model = None

        paginator = TenItemPagination()
        paginated_notes = paginator.paginate_queryset(notes, request)
        serializers = NoteSerializer(paginated_notes, many=True)

        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).exists()
        notify = True if unread_notifications else False

        total_items = paginator.page.paginator.count
        current_page = paginator.page.number
        total_pages = paginator.page.paginator.num_pages

        return Response(
            {
                "message": "팔로우 노트 홈 조회",
                "total_items": total_items,
                "current_page": current_page,
                "total_pages": total_pages,
                "data": {"notify": notify, "content": serializers.data},
            },
            status=status.HTTP_200_OK,
        )
