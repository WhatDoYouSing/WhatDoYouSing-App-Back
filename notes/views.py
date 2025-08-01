from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import (
    Notes,
    NoteComment,
    NoteEmotion,
    Emotions,
    Plis,
    NoteBlock,
    PliBlock,
    UserBlock,
)
from collects.models import ScrapNotes
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError
from social.models import *
from django.db.models import Q
from home.serializers import *
from django.db.models import F
from .serializers import *
from django.db.models import Count


class NoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, note_id):
        # 노트 가져오기
        note = get_object_or_404(Notes, id=note_id)

        # 댓글 가져오기
        comments = NoteComment.objects.filter(note=note).order_by("-created_at")

        # 감정 개수 가져오기
        emotion_counts = (
            NoteEmotion.objects.filter(note=note)
            .values("emotion__name")
            .annotate(count=Count("id"))
        )

        # 태그 가져오기
        tags = (
            list(note.tag_time.values_list("name", flat=True))
            + list(note.tag_season.values_list("name", flat=True))
            + list(note.tag_context.values_list("name", flat=True))
        )

        user = request.user
        is_mine = note.user == user

        # is_collected: 내가 보관했는지
        is_collected = ScrapNotes.objects.filter(
            scrap_list__user=user, content_id=note.id
        ).exists()

        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values_list(
                    "follower", flat=True
                )
            )
        ).values_list("following", flat=True)

        # same_user 이 노트를 쓴 사람의 다른 콘텐츠 ====================
        visibility_filter = ["public"]
        if note.user == user:
            visibility_filter = ["public", "friends", "private"]
        elif note.user.id in friends:
            visibility_filter = ["public", "friends"]

        same_user_notes = (
            Notes.objects.filter(user=note.user, visibility__in=visibility_filter)
            .exclude(id=note.id)
            .order_by("-created_at")[:2]
        )
        same_user_plis = Plis.objects.filter(
            user=note.user, visibility__in=visibility_filter
        ).order_by("-created_at")[:2]
        same_user = list(NoteSerializer(same_user_notes, many=True).data) + list(
            PliSerializer(same_user_plis, many=True).data
        )
        same_user = sorted(same_user, key=lambda x: x["created_at"], reverse=True)[:2]

        # 이 노래의 다른 노트 보기 =====================================

        filtered_notes = (
            Notes.objects.filter(
                Q(
                    user=user, song_title=note.song_title, artist=note.artist
                )  #  내 노트는 다 포함
                | Q(
                    user__in=friends,
                    visibility="friends",
                    song_title=note.song_title,
                    artist=note.artist,
                )  # 친구면 friends 포함
                | Q(
                    visibility="public", song_title=note.song_title, artist=note.artist
                )  #  일반 사용자는 public만
            )
            .exclude(id=note.id)
            .order_by("-created_at")[:2]
        )

        same_song = NoteSerializer(filtered_notes, many=True).data

        # 이 노래를 인용한 플리 보기 =====================================

        # 해당 노트의 `song_title` & `artist`와 동일한 노트를 포함하는 `PliNotes` 찾기
        related_pli_ids = PliNotes.objects.filter(
            notes__song_title=note.song_title, notes__artist=note.artist
        ).values_list("plis", flat=True)

        # 플리 필터링 (visibility 적용)
        same_pli = PliSerializer(
            Plis.objects.filter(
                id__in=related_pli_ids, visibility__in=visibility_filter
            ).order_by("-created_at")[:2],
            many=True,
        ).data

        # =======================================================

        # 노트 데이터를 반환
        note_data = {
            "id": note.id,
            "user": {
                "id": note.user.id,
                "username": note.user.serviceID,
                "nickname": note.user.nickname,
                "profile": note.user.profile,
            },
            "mine": is_mine,
            "is_collected": is_collected,
            "created_at": note.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_updated": note.is_updated,
            "visibility": note.visibility,
            "emotion": note.emotion.name,
            "song_title": note.song_title,
            "artist": note.artist,
            "album_art": note.album_art,
            "memo": note.memo,
            "link": note.link,
            "lyrics": note.lyrics,
            "tags": tags,
            "location_name": note.location_name,
            "location_address": note.location_address,
            "emotions": [
                {"emotion": e["emotion__name"], "count": e["count"]}
                for e in emotion_counts
            ],
            "comment_count": comments.count(),
            "scrap_count": ScrapNotes.objects.filter(content_id=note.id).count(),
            "comment": [
                {
                    "user": {
                        "id": c.user.id,
                        "username": c.user.serviceID,
                        "nickname": c.user.nickname,
                        "profile": c.user.profile,
                    },
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
                    "content": c.content,
                    "reply_count": c.replies.count(),
                    "likes_count": c.likes.count(),
                    "mine": c.user == user,
                }
                for c in comments[:1]  # 최근 1개만 반환
            ],
            "same_user": same_user,
            "same_song": same_song,
            "same_pli": same_pli,
        }

        return Response(
            {"message": "노트 상세 조회 성공", "data": note_data},
            status=status.HTTP_200_OK,
        )


class NoteEmotionToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, note_id, emotion_name):
        user = request.user  # 현재 요청한 사용자
        note = get_object_or_404(Notes, id=note_id)
        emotion = get_object_or_404(Emotions, name=emotion_name)

        # 기존 감정이 있는지 확인
        existing_emotion = NoteEmotion.objects.filter(
            note=note, user=user, emotion=emotion
        ).first()

        if existing_emotion:
            # 이미 감정이 있으면 삭제 (감정 취소)
            existing_emotion.delete()
            Emotions.objects.filter(id=emotion.id).update(count=F("count") - 1)
            return Response(
                {"message": f"'{emotion_name}' 감정이 취소되었습니다."},
                status=status.HTTP_200_OK,
            )
        else:
            # 새로운 감정 추가
            try:
                NoteEmotion.objects.create(note=note, user=user, emotion=emotion)
                Emotions.objects.filter(id=emotion.id).update(count=F("count") + 1)
                return Response(
                    {"message": f"'{emotion_name}' 감정이 추가되었습니다."},
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError:
                return Response(
                    {"error": "감정 추가 중 오류가 발생했습니다."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class SameUserContentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user_owner = get_object_or_404(User, id=user_id)
        user = request.user

        # 친구 관계 확인 (서로 팔로우한 경우)
        is_friend = (
            UserFollows.objects.filter(follower=user, following=user_owner).exists()
            and UserFollows.objects.filter(follower=user_owner, following=user).exists()
        )

        # 사용자 유형별 필터링
        if user_id == user.id:
            # 본인: 모든 콘텐츠 조회
            notes = Notes.objects.filter(user=user_owner)
            plis = Plis.objects.filter(user=user_owner)
            message = f"본인 {user_owner.nickname}님의 다른 글 목록 조회"
        elif is_friend:
            # 친구: 공개 + 친구 공개 콘텐츠만 조회
            notes = Notes.objects.filter(
                user=user_owner, visibility__in=["public", "friends"]
            )
            plis = Plis.objects.filter(
                user=user_owner, visibility__in=["public", "friends"]
            )
            message = f"친구 {user_owner.nickname}님의 다른 글 목록 조회"
        else:
            # 일반 사용자: 공개 콘텐츠만 조회
            notes = Notes.objects.filter(user=user_owner, visibility="public")
            plis = Plis.objects.filter(user=user_owner, visibility="public")
            message = f"{user_owner.nickname}님의 다른 글 목록 조회"

        # 직렬화 및 최신순 정렬
        combined_data = list(NoteSerializer(notes, many=True).data) + list(
            PliSerializer(plis, many=True).data
        )
        combined_data.sort(key=lambda x: x["created_at"], reverse=True)

        return Response(
            {"message": message, "data": combined_data}, status=status.HTTP_200_OK
        )


class SameSongNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, note_id):
        note = get_object_or_404(Notes, id=note_id)
        user = request.user

        # 친구 리스트 가져오기 (서로 팔로우한 경우)
        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values_list(
                    "follower", flat=True
                )
            )
        ).values_list("following", flat=True)

        filtered_notes = (
            Notes.objects.filter(
                Q(
                    user=user, song_title=note.song_title, artist=note.artist
                )  # ✅ 내 노트는 다 포함
                | Q(
                    user__in=friends,
                    visibility="friends",
                    song_title=note.song_title,
                    artist=note.artist,
                )  # ✅ 친구면 friends 포함
                | Q(
                    visibility="public", song_title=note.song_title, artist=note.artist
                )  # ✅ 일반 사용자는 public만
            )
            .exclude(id=note.id)
            .order_by("-created_at")
        )

        serialized_notes = NoteSerializer(filtered_notes, many=True).data

        return Response(
            {
                "message": f"'{note.song_title} - {note.artist}'와 같은 노래를 사용한 노트 목록 조회",
                "data": serialized_notes,
            },
            status=200,
        )


class SameSongPliView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, note_id):
        note = get_object_or_404(Notes, id=note_id)
        user = request.user

        # 친구 리스트 가져오기 (서로 팔로우한 경우)
        friends = UserFollows.objects.filter(
            Q(follower=user)
            & Q(
                following__in=UserFollows.objects.filter(following=user).values_list(
                    "follower", flat=True
                )
            )
        ).values_list("following", flat=True)

        # 해당 노트의 `song_title` & `artist`와 동일한 노트를 포함하는 `PliNotes` 찾기
        related_pli_ids = PliNotes.objects.filter(
            notes__song_title=note.song_title, notes__artist=note.artist
        ).values_list("plis", flat=True)

        # 플리 필터링 (visibility 적용)
        filtered_plis = (
            Plis.objects.filter(id__in=related_pli_ids)
            .filter(
                Q(user=user)  # 본인 → 모든 플리 포함
                | Q(
                    user__in=friends, visibility__in=["public", "friends"]
                )  # 친구 → friends + public 포함
                | Q(visibility="public")  # 일반 사용자 → public만 포함
            )
            .order_by("-created_at")
        )

        # 직렬화하여 최신순 정렬 후 반환
        serialized_plis = PliSerializer(filtered_plis, many=True).data

        return Response(
            {
                "message": f"'{note.song_title} - {note.artist}'를 포함한 플리 목록 조회",
                "data": serialized_plis,
            },
            status=200,
        )


class NoteCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, note_id):
        user = request.user
        note = get_object_or_404(Notes, id=note_id)
        content = request.data.get("content")
        comment_id = request.data.get("comment_id", None)

        if not content:
            return Response(
                {"error": "댓글 내용을 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if comment_id:
            # 대댓글 작성
            parent_comment = get_object_or_404(NoteComment, id=comment_id, note=note)
            reply = NoteReply.objects.create(
                comment=parent_comment,
                user=user,
                content=content,
                mention=request.data.get("mention"),
            )
            return Response(
                {
                    "message": "대댓글이 등록되었습니다.",
                    "data": NoteReplySerializer(reply).data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            # 일반 댓글 작성
            comment = NoteComment.objects.create(note=note, user=user, content=content)
            return Response(
                {
                    "message": "댓글이 등록되었습니다.",
                    "data": NoteCommentSerializer(comment).data,
                },
                status=status.HTTP_201_CREATED,
            )


class NoteCommentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, note_id):
        user = request.user
        note = get_object_or_404(Notes, id=note_id)

        # 댓글 개수 & 스크랩 개수
        comment_count = NoteComment.objects.filter(note=note).count()
        scrap_count = ScrapNotes.objects.filter(content_id=note_id).count()

        # 부모 댓글 (최상위 댓글) 가져오기
        comments = NoteComment.objects.filter(note=note).order_by("created_at")

        # 댓글 직렬화
        serialized_comments = []
        for comment in comments:
            replies = NoteReply.objects.filter(comment=comment).order_by("created_at")

            serialized_replies = [
                {
                    "id": reply.id,
                    "user": {
                        "id": reply.user.id,
                        "username": reply.user.serviceID,
                        "nickname": reply.user.nickname,
                        "profile": reply.user.profile,
                    },
                    "parent_nickname": comment.user.nickname,  # 부모 댓글의 닉네임 (언급된 닉네임)
                    "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M"),
                    "content": reply.content,
                    "likes_count": reply.likes.count(),
                    "mine": reply.user == user,  # 현재 유저가 작성한 경우 true
                }
                for reply in replies
            ]

            serialized_comments.append(
                {
                    "id": comment.id,
                    "user": {
                        "id": comment.user.id,
                        "username": comment.user.serviceID,
                        "nickname": comment.user.nickname,
                        "profile": comment.user.profile,
                    },
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                    "content": comment.content,
                    "reply_count": replies.count(),
                    "likes_count": comment.likes.count(),
                    "mine": comment.user == user,  # 현재 유저가 작성한 경우 true
                    "replies": serialized_replies,
                }
            )

        return Response(
            {
                "message": "댓글 조회 성공",
                "data": {
                    "comment_count": comment_count,
                    "scrap_count": scrap_count,
                    "comments": serialized_comments,
                },
            },
            status=status.HTTP_200_OK,
        )


class NoteCommentEditDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    # 댓글 삭제 (본인만 가능)
    def delete(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(NoteComment, id=comment_id)

        if comment.user != user:
            return Response(
                {"error": "본인의 댓글만 삭제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        comment.delete()
        return Response(
            {"message": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )

    # 댓글 수정 (본인만 가능)
    def patch(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(NoteComment, id=comment_id)

        if comment.user != user:
            return Response(
                {"error": "본인의 댓글만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response(
                {"error": "내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        comment.content = new_content
        comment.save()

        return Response(
            {"message": "댓글이 수정되었습니다."}, status=status.HTTP_200_OK
        )


class NoteReplyEditDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    # 대댓글 삭제 (본인만 가능)
    def delete(self, request, reply_id):
        user = request.user
        reply = get_object_or_404(NoteReply, id=reply_id)

        if reply.user != user:
            return Response(
                {"error": "본인의 대댓글만 삭제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        reply.delete()
        return Response(
            {"message": "대댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )

    # 대댓글 수정 (본인만 가능)
    def patch(self, request, reply_id):

        user = request.user
        reply = get_object_or_404(NoteReply, id=reply_id)

        if reply.user != user:
            return Response(
                {"error": "본인의 대댓글만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response(
                {"error": "내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        reply.content = new_content
        reply.save()

        return Response(
            {"message": "대댓글이 수정되었습니다."}, status=status.HTTP_200_OK
        )


class ReportCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, content_type, comment_type, content_id):
        user = request.user
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"message": "신고 사유를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model = None
        report_type = None

        if content_type == "note":
            if comment_type == "comment":
                model = NoteComment
                report_type = "note comment"
            elif comment_type == "reply":
                model = NoteReply
                report_type = "note reply"
        elif content_type == "pli":
            if comment_type == "comment":
                model = PliComment
                report_type = "playlist comment"
            elif comment_type == "reply":
                model = PliReply
                report_type = "playlist reply"

        # 대상 가져오기
        target = get_object_or_404(model, id=content_id)

        # 신고 생성
        CommentReport.objects.create(
            report_user=user,
            issue_user=target.user,
            content=target.content,
            reason=reason,
            type=report_type,
            content_id=target.id,
        )

        return Response(
            {"message": f"{report_type}이(가) 신고되었습니다."},
            status=status.HTTP_201_CREATED,
        )


# ───────────────────────── 게시글 차단/차단 해제 ──────────────────────────
class BlockNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # 노트 차단
        NoteBlock.objects.get_or_create(user=request.user, note_id=pk)
        return Response({"message": "노트 차단 완료"}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        # 노트 차단 해제
        NoteBlock.objects.filter(user=request.user, note_id=pk).delete()
        return Response(
            {"message": "노트 차단 해제"}, status=status.HTTP_204_NO_CONTENT
        )


class BlockPliView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        PliBlock.objects.get_or_create(user=request.user, pli_id=pk)
        return Response({"message": "플리 차단 완료"}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        PliBlock.objects.filter(user=request.user, pli_id=pk).delete()
        return Response(
            {"message": "플리 차단 해제"}, status=status.HTTP_204_NO_CONTENT
        )


# ───────────────────────── 게시글 작성자 차단/차단 해제 ────────────────────
class BlockNoteAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        note = get_object_or_404(Notes, id=pk)
        if note.user == request.user:
            return Response(
                {"message": "자기 자신은 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UserBlock.objects.get_or_create(user=request.user, blocked_user=note.user)
        return Response(
            {"message": "노트 작성자 차단 완료"}, status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        note = get_object_or_404(Notes, id=pk)
        UserBlock.objects.filter(user=request.user, blocked_user=note.user).delete()
        return Response(
            {"message": "노트 작성자 차단 해제"}, status=status.HTTP_204_NO_CONTENT
        )


class BlockPliAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        pli = get_object_or_404(Plis, id=pk)
        if pli.user == request.user:
            return Response(
                {"message": "자기 자신은 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UserBlock.objects.get_or_create(user=request.user, blocked_user=pli.user)
        return Response(
            {"message": "플리 작성자 차단 완료"}, status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        pli = get_object_or_404(Plis, id=pk)
        UserBlock.objects.filter(user=request.user, blocked_user=pli.user).delete()
        return Response(
            {"message": "플리 작성자 차단 해제"}, status=status.HTTP_204_NO_CONTENT
        )
