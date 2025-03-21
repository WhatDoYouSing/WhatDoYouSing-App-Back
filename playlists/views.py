from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import status
from notes.models import Plis, PliNotes, NoteComment
from collects.models import ScrapPlaylists
from notes.models import Notes, NoteEmotion
from accounts.models import User
from social.models import UserFollows
from home.serializers import *
from .serializers import *

class PlaylistDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        user = request.user
        pli = get_object_or_404(Plis, id=pk)
        pli_owner = pli.user

        # 친구 여부 확인
        is_friend = UserFollows.objects.filter(
            Q(follower=user, following=pli_owner) & Q(follower=pli_owner, following=user)
        ).exists()

        # 접근 권한 체크 (본인/친구/타인)
        if pli_owner == user or pli.visibility == "public" or (is_friend and pli.visibility == "friends"):
            can_access = True
        else:
            return Response({"error": "이 플리를 볼 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # 플리에 포함된 노트 리스트 가져오기
        pli_notes = PliNotes.objects.filter(plis=pli)
        note_data = []
        for pli_note in pli_notes:
            note = pli_note.notes

            # 노트 접근 권한 확인
            if note.user == user or note.visibility == "public" or (is_friend and note.visibility == "friends"):
                can_access_note = True
            else:
                can_access_note = False

            note_data.append({
                "id": note.id,
                "song_title": note.song_title,
                "artist": note.artist,
                "lyrics": note.lyrics,
                "memo": note.memo,
                "nickname": note.user.nickname,
                "emotion": note.emotion.name if note.emotion else None,
                "album_art": note.album_art,
                "note_memo": pli_note.note_memo,
                "can_access": can_access_note
            })

        # 태그 리스트 가져오기
        tags = list(pli.tag_time.values_list("name", flat=True)) + \
               list(pli.tag_season.values_list("name", flat=True)) + \
               list(pli.tag_context.values_list("name", flat=True))

        # 댓글 가져오기 (최신순)
        comments = PliComment.objects.filter(pli__in=pli_notes.values_list("plis", flat=True)).order_by('-created_at')
        comment = comments.first()

        serialized_comments=[]
        if comment is not None:

            serialized_comments = [{
                "user": {
                    "id": comment.user.id,
                    "username": comment.user.username,
                    "nickname": comment.user.nickname,
                    "profile": comment.user.profile
                },
                "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M'),
                "content": comment.content,
                "reply_count": comment.replies.count(),
                "likes_count": comment.likes.count(),
                "mine": comment.user == request.user 
            } ]

        # 같은 유저의 다른 게시글 가져오기
        same_user_plis = Plis.objects.filter(user=pli_owner).exclude(id=pli.id)[:2]
        serialized_same_user_plis = PliSerializer(same_user_plis, many=True)


        # 최종 데이터 구성
        pli_data = {
            "id": pli.id,
            "title": pli.title,
            "user": {
                "id": pli.user.id,
                "username": pli.user.username,
                "nickname": pli.user.nickname,
                "profile": pli.user.profile
            },
            "created_at": pli.created_at.strftime('%Y-%m-%d %H:%M'),
            "is_updated": pli.is_updated,
            "visibility": pli.visibility,
            "contents": note_data,
            "tags": tags,
            "likes_count": pli.comments_count,  # 좋아요 수 (임시)
            "scrap_count": ScrapPlaylists.objects.filter(content_id=pli.id).count(),
            "comment_count": comments.count(),
            "comment": serialized_comments,
            "same_user": serialized_same_user_plis.data
        }

        return Response({
            "message": "플리 상세 조회 성공",
            "data": pli_data
        }, status=status.HTTP_200_OK)



class SameUserPliView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        user_owner = get_object_or_404(User, id=user_id)
        user = request.user

        # 친구 관계 확인 (서로 팔로우한 경우)
        is_friend = UserFollows.objects.filter(
            Q(follower=user, following=user_owner) &
            Q(follower=user_owner, following=user)
        ).exists()

        # 사용자 유형별 필터링
        if user_id == user.id:
            # 본인: 모든 콘텐츠 조회
            plis = Plis.objects.filter(user=user_owner)
            message = f"본인 {user_owner.nickname}님의 다른 플리 목록 조회"
        elif is_friend:
            # 친구: 공개 + 친구 공개 콘텐츠만 조회
            plis = Plis.objects.filter(user=user_owner, visibility__in=['public', 'friends'])
            message = f"친구 {user_owner.nickname}님의 다른 플리 목록 조회"
        else:
            # 일반 사용자: 공개 콘텐츠만 조회
            plis = Plis.objects.filter(user=user_owner, visibility='public')
            message = f"{user_owner.nickname}님의 다른 플리 목록 조회"

        # 직렬화 및 최신순 정렬
        plis = plis.order_by('-created_at')
        serialiser_data = PliSerializer(plis, many=True).data
    
        return Response({
            "message": message,
            "data": serialiser_data
        }, status=status.HTTP_200_OK)


class PliCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pli_id):
        user = request.user
        pli = get_object_or_404(Plis, id=pli_id)
        content = request.data.get("content")
        comment_id = request.data.get("comment_id", None)

        if not content:
            return Response({"error": "댓글 내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        if comment_id:
            # 대댓글 작성
            parent_comment = get_object_or_404(PliComment, id=comment_id, pli=pli)
            reply = PliReply.objects.create(
                comment=parent_comment,
                user=user,
                content=content,
                mention=request.data.get("mention")
            )
            return Response(
                {"message": "대댓글이 등록되었습니다.", "data": PliReplySerializer(reply).data},
                status=status.HTTP_201_CREATED
            )
        else:
            # 일반 댓글 작성
            comment = PliComment.objects.create(
                pli=pli,
                user=user,
                content=content
            )
            return Response(
                {"message": "댓글이 등록되었습니다.", "data": PliCommentSerializer(comment).data},
                status=status.HTTP_201_CREATED
            )
        

class PliCommentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pli_id):
        user = request.user
        pli = get_object_or_404(Plis, id=pli_id)

        # 댓글 개수 & 스크랩 개수
        comment_count = PliComment.objects.filter(pli=pli).count()
        scrap_count = ScrapPlaylists.objects.filter(content_id=pli_id).count()

        # 부모 댓글 (최상위 댓글) 가져오기
        comments = PliComment.objects.filter(pli=pli).order_by('created_at')

        # 댓글 직렬화
        serialized_comments = []
        for comment in comments:
            replies = PliReply.objects.filter(comment=comment).order_by('created_at')

            serialized_replies = [{
                "id": reply.id,
                "user": {
                    "id": reply.user.id,
                    "username": reply.user.username,
                    "nickname": reply.user.nickname,
                    "profile": reply.user.profile
                },
                "parent_nickname": comment.user.nickname,  # 부모 댓글의 닉네임 (언급된 닉네임)
                "created_at": reply.created_at.strftime('%Y-%m-%d %H:%M'),
                "content": reply.content,
                "likes_count": reply.likes.count(),
                "mine": reply.user == user  # 현재 유저가 작성한 경우 true
            } for reply in replies]

            serialized_comments.append({
                "id": comment.id,
                "user": {
                    "id": comment.user.id,
                    "username": comment.user.username,
                    "nickname": comment.user.nickname,
                    "profile": comment.user.profile
                },
                "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M'),
                "content": comment.content,
                "reply_count": replies.count(),
                "likes_count": comment.likes.count(),
                "mine": comment.user == user,  # 현재 유저가 작성한 경우 true
                "replies": serialized_replies
            })

        return Response({
            "message": "플리 댓글 조회 성공",
            "data": {
                "comment_count": comment_count,
                "scrap_count": scrap_count,
                "comments": serialized_comments
            }
        }, status=status.HTTP_200_OK)
    


class PliCommentEditDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    # 댓글 삭제 (본인만 가능)
    def delete(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(PliComment, id=comment_id)

        if comment.user != user:
            return Response({"error": "본인의 댓글만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"message": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

    # 댓글 수정 (본인만 가능)
    def patch(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(PliComment, id=comment_id)

        if comment.user != user:
            return Response({"error": "본인의 댓글만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response({"error": "내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        comment.content = new_content
        comment.save()

        return Response({"message": "댓글이 수정되었습니다."}, status=status.HTTP_200_OK)
    

class PliReplyEditDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    # 대댓글 삭제 (본인만 가능)
    def delete(self, request, reply_id):
        user = request.user
        reply = get_object_or_404(PliReply, id=reply_id)

        if reply.user != user:
            return Response({"error": "본인의 대댓글만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        reply.delete()
        return Response({"message": "대댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

    # 대댓글 수정 (본인만 가능)
    def patch(self, request, reply_id):
        
        user = request.user
        reply = get_object_or_404(PliReply, id=reply_id)

        if reply.user != user:
            return Response({"error": "본인의 대댓글만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response({"error": "내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        reply.content = new_content
        reply.save()

        return Response({"message": "대댓글이 수정되었습니다."}, status=status.HTTP_200_OK)
