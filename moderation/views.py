from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from moderation.serializers import BlockActionSerializer
from moderation.models import (
    UserBlock,
    NoteBlock,
    PliBlock,
    NoteCommentBlock,
    NoteReplyBlock,
    PliCommentBlock,
    PliReplyBlock,
)
from notes.models import Notes, Plis, NoteComment, NoteReply, PliComment, PliReply
from social.models import UserFollows
from collects.models import ScrapNotes, ScrapPlaylists, ScrapList

User = get_user_model()


class BlockingView(APIView):
    permission_classes = [IsAuthenticated]

    # ───────────── 차단 목록 조회 ─────────────
    def get(self, request):
        u = request.user
        return Response(
            {
                "blocked_users": list(
                    UserBlock.objects.filter(blocker=u).values_list(
                        "blocked_user_id", flat=True
                    )
                ),
                "blocked_notes": list(
                    NoteBlock.objects.filter(blocker=u).values_list(
                        "note_id", flat=True
                    )
                ),
                "blocked_plis": list(
                    PliBlock.objects.filter(blocker=u).values_list("pli_id", flat=True)
                ),
                "blocked_notecomment": list(
                    NoteCommentBlock.objects.filter(blocker=u).values_list(
                        "comment_id", flat=True
                    )
                ),
                "blocked_plicomment": list(
                    PliCommentBlock.objects.filter(blocker=u).values_list(
                        "comment_id", flat=True
                    )
                ),
                "blocked_notereply": list(
                    NoteReplyBlock.objects.filter(blocker=u).values_list(
                        "reply_id", flat=True
                    )
                ),
                "blocked_plireply": list(
                    PliReplyBlock.objects.filter(blocker=u).values_list(
                        "reply_id", flat=True
                    )
                ),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        ser = BlockActionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        target_type, target_id = ser.validated_data.values()

        u = request.user

        # ────── ① User 차단 ──────
        if target_type == "user":
            if target_id == u.pk:
                raise ValidationError({"detail": "자기 자신은 차단할 수 없습니다."})
            if not User.objects.filter(pk=target_id).exists():
                raise ValidationError({"detail": "해당 사용자가 존재하지 않습니다."})

            blocked_user = User.objects.get(pk=target_id)
            _, created = UserBlock.objects.get_or_create(
                blocker=u, blocked_user=blocked_user
            )

            # 팔로우 해제
            UserFollows.objects.filter(follower=u, following=blocked_user).delete()
            UserFollows.objects.filter(follower=blocked_user, following=u).delete()

            # ✅ 차단과 동시에 해당 유저의 노트/플리를 스크랩에서 제거
            if created:
                my_scrap_lists = ScrapList.objects.filter(user=u)
                note_ids = Notes.objects.filter(user=blocked_user).values_list(
                    "id", flat=True
                )
                pli_ids = Plis.objects.filter(user=blocked_user).values_list(
                    "id", flat=True
                )

                ScrapNotes.objects.filter(
                    scrap_list__in=my_scrap_lists, content_id__in=note_ids
                ).delete()
                ScrapPlaylists.objects.filter(
                    scrap_list__in=my_scrap_lists, content_id__in=pli_ids
                ).delete()

        # ────── ② Note 차단 ──────
        elif target_type == "note":
            note = Notes.objects.filter(pk=target_id).first()
            if not note:
                raise ValidationError({"detail": "해당 노트가 존재하지 않습니다."})
            if note.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 노트는 차단할 수 없습니다."}
                )

            _, created = NoteBlock.objects.get_or_create(blocker=u, note=note)

            # ✅ 보관함에서 해당 노트 삭제
            if created:
                my_scrap_lists = ScrapList.objects.filter(user=u)
                ScrapNotes.objects.filter(
                    scrap_list__in=my_scrap_lists, content_id=note.id
                ).delete()

        # ────── ③ Pli 차단 ──────
        elif target_type == "pli":
            pli = Plis.objects.filter(pk=target_id).first()
            if not pli:
                raise ValidationError({"detail": "해당 플리가 존재하지 않습니다."})
            if pli.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 플리는 차단할 수 없습니다."}
                )

            _, created = PliBlock.objects.get_or_create(blocker=u, pli=pli)

            # ✅ 보관함에서 해당 플리 삭제
            if created:
                my_scrap_lists = ScrapList.objects.filter(user=u)
                ScrapPlaylists.objects.filter(
                    scrap_list__in=my_scrap_lists, content_id=pli.id
                ).delete()

        # ────── ④ Note 댓글 차단 ──────
        elif target_type == "note_comment":
            comment = NoteComment.objects.filter(pk=target_id).first()
            if not comment:
                raise ValidationError({"detail": "해당 댓글이 존재하지 않습니다."})
            if comment.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 댓글은 차단할 수 없습니다."}
                )

            _, created = NoteCommentBlock.objects.get_or_create(
                blocker=u, comment=comment
            )

        # ────── ⑤ Note 대댓글 차단 ──────
        elif target_type == "note_reply":
            reply = NoteReply.objects.filter(pk=target_id).first()
            if not reply:
                raise ValidationError({"detail": "해당 대댓글이 존재하지 않습니다."})
            if reply.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 대댓글은 차단할 수 없습니다."}
                )

            _, created = NoteReplyBlock.objects.get_or_create(blocker=u, reply=reply)

        # ────── ⑥ Pli 댓글 차단 ──────
        elif target_type == "pli_comment":
            comment = PliComment.objects.filter(pk=target_id).first()
            if not comment:
                raise ValidationError({"detail": "해당 댓글이 존재하지 않습니다."})
            if comment.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 댓글은 차단할 수 없습니다."}
                )

            _, created = PliCommentBlock.objects.get_or_create(
                blocker=u, comment=comment
            )

        # ────── ⑦ Pli 대댓글 차단 ──────
        elif target_type == "pli_reply":
            reply = PliReply.objects.filter(pk=target_id).first()
            if not reply:
                raise ValidationError({"detail": "해당 대댓글이 존재하지 않습니다."})
            if reply.user_id == u.pk:
                raise ValidationError(
                    {"detail": "자신이 쓴 대댓글은 차단할 수 없습니다."}
                )

            _, created = PliReplyBlock.objects.get_or_create(blocker=u, reply=reply)

        if "created" not in locals():
            raise ValidationError({"detail": "알 수 없는 차단 대상입니다."})

        return Response(
            {
                "message": "차단 완료" if created else "이미 차단된 대상입니다.",
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    """ # ───────────── 차단 추가 ─────────────
    def post(self, request):
        ser = BlockActionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        target_type, target_id = ser.validated_data.values()

        # ────── ① User 차단 ──────
        if target_type == "user":
            if target_id == request.user.pk:  # ★ 자기 자신
                raise ValidationError({"detail": "자기 자신은 차단할 수 없습니다."})
            if not User.objects.filter(pk=target_id).exists():  # 존재 확인
                raise ValidationError({"detail": "해당 사용자가 존재하지 않습니다."})
            _, created = UserBlock.objects.get_or_create(
                blocker=request.user, blocked_user_id=target_id
            )
            # 차단과 동시에 팔로우 관계 해제
            UserFollows.objects.filter(
                follower=request.user, following_id=target_id
            ).delete()
            UserFollows.objects.filter(
                follower_id=target_id, following=request.user
            ).delete()

        # ────── ② Note 차단 ──────
        elif target_type == "note":
            note = Notes.objects.filter(pk=target_id).first()
            if not note:  # 존재 확인
                raise ValidationError({"detail": "해당 노트가 존재하지 않습니다."})
            if note.user_id == request.user.pk:  # ★ 내 글
                raise ValidationError(
                    {"detail": "자신이 쓴 노트는 차단할 수 없습니다."}
                )
            _, created = NoteBlock.objects.get_or_create(
                blocker=request.user, note=note
            )

        # ────── ③ Pli 차단 ──────
        else:  # target_type == "pli"
            pli = Plis.objects.filter(pk=target_id).first()
            if not pli:
                raise ValidationError({"detail": "해당 플리가 존재하지 않습니다."})
            if pli.user_id == request.user.pk:  # ★ 내 글
                raise ValidationError(
                    {"detail": "자신이 쓴 플리는 차단할 수 없습니다."}
                )
            _, created = PliBlock.objects.get_or_create(blocker=request.user, pli=pli)

        return Response(
            {
                "message": "차단 완료" if created else "이미 차단된 대상입니다.",
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # ───────────── 차단 해제 미지원 ─────────────
    def delete(self, request, *args, **kwargs):
        return Response(
            {"message": "차단 해제 기능은 지원되지 않습니다."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
 """
