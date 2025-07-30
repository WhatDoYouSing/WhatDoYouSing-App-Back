# from django.shortcuts import render
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, generics
# from django.shortcuts import get_object_or_404
# from notes.models import (
#     Notes,
#     NoteComment,
#     NoteEmotion,
#     Emotions,
#     Plis,
# )
# from .models import *
# from collects.models import ScrapNotes
# from rest_framework.permissions import IsAuthenticated
# from django.db import IntegrityError
# from social.models import *
# from django.db.models import Q
# from home.serializers import *
# from django.db.models import F
# from .serializers import *
# from django.db.models import Count


# # Create your views here.
# # ───────────────────────── 게시글 차단/차단 해제 ──────────────────────────
# class BlockNoteView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         # 노트 차단
#         NoteBlock.objects.get_or_create(user=request.user, note_id=pk)
#         return Response({"message": "노트 차단 완료"}, status=status.HTTP_201_CREATED)

#     def delete(self, request, pk):
#         # 노트 차단 해제
#         NoteBlock.objects.filter(user=request.user, note_id=pk).delete()
#         return Response(
#             {"message": "노트 차단 해제"}, status=status.HTTP_204_NO_CONTENT
#         )


# class BlockPliView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         PliBlock.objects.get_or_create(user=request.user, pli_id=pk)
#         return Response({"message": "플리 차단 완료"}, status=status.HTTP_201_CREATED)

#     def delete(self, request, pk):
#         PliBlock.objects.filter(user=request.user, pli_id=pk).delete()
#         return Response(
#             {"message": "플리 차단 해제"}, status=status.HTTP_204_NO_CONTENT
#         )


# # ───────────────────────── 게시글 작성자 차단/차단 해제 ────────────────────
# class BlockNoteAuthorView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         note = get_object_or_404(Notes, id=pk)
#         if note.user == request.user:
#             return Response(
#                 {"message": "자기 자신은 차단할 수 없습니다."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         UserBlock.objects.get_or_create(user=request.user, blocked_user=note.user)
#         return Response(
#             {"message": "노트 작성자 차단 완료"}, status=status.HTTP_201_CREATED
#         )

#     def delete(self, request, pk):
#         note = get_object_or_404(Notes, id=pk)
#         UserBlock.objects.filter(user=request.user, blocked_user=note.user).delete()
#         return Response(
#             {"message": "노트 작성자 차단 해제"}, status=status.HTTP_204_NO_CONTENT
#         )


# class BlockPliAuthorView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         pli = get_object_or_404(Plis, id=pk)
#         if pli.user == request.user:
#             return Response(
#                 {"message": "자기 자신은 차단할 수 없습니다."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         UserBlock.objects.get_or_create(user=request.user, blocked_user=pli.user)
#         return Response(
#             {"message": "플리 작성자 차단 완료"}, status=status.HTTP_201_CREATED
#         )

#     def delete(self, request, pk):
#         pli = get_object_or_404(Plis, id=pk)
#         UserBlock.objects.filter(user=request.user, blocked_user=pli.user).delete()
#         return Response(
#             {"message": "플리 작성자 차단 해제"}, status=status.HTTP_204_NO_CONTENT
#         )


# class BlockNoteView(generics.GenericAPIView):
#     serializer_class = NoteBlockSerializer
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         # serializer가 note_id 값을 검증
#         serializer = self.get_serializer(data={"note_id": pk})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"message": "노트 차단 완료"}, status=201)

#     def delete(self, request, pk):
#         NoteBlock.objects.filter(user=request.user, note_id=pk).delete()
#         return Response({"message": "노트 차단 해제"}, status=204)


# class BlockPliView(generics.GenericAPIView):
#     serializer_class = PliBlockSerializer
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         serializer = self.get_serializer(data={"pli_id": pk})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"message": "플리 차단 완료"}, status=201)

#     def delete(self, request, pk):
#         PliBlock.objects.filter(user=request.user, pli_id=pk).delete()
#         return Response({"message": "플리 차단 해제"}, status=204)


# # ───────────────────────────────── 작성자 차단/해제 ──────────────────────────
# class BlockAuthorView(generics.GenericAPIView):
#     """
#     공통 작성자 차단: 노트/플리 구분 없이 작성자 PK만 전달
#       POST   /uploads/author-block/{user_id}/
#       DELETE /uploads/author-block/{user_id}/
#     """

#     serializer_class = AuthorBlockSerializer
#     permission_classes = [IsAuthenticated]

#     def post(self, request, user_id):
#         serializer = self.get_serializer(data={"blocked_user_id": user_id})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"message": "작성자 차단 완료"}, status=201)

#     def delete(self, request, user_id):
#         UserBlock.objects.filter(user=request.user, blocked_user_id=user_id).delete()
#         return Response({"message": "작성자 차단 해제"}, status=204)

# moderation/views.py
# moderation/views.py
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from moderation.serializers import BlockActionSerializer
from moderation.models import UserBlock, NoteBlock, PliBlock
from notes.models import Notes, Plis

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
            },
            status=status.HTTP_200_OK,
        )

    # ───────────── 차단 추가 ─────────────
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
