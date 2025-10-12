from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notes.models import *
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import *
from home.serializers import *
from moderation.mixins import BlockFilterMixin
from moderation.models import UserBlock, NoteBlock, PliBlock


class CollectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, type, scrap_list_id, content_id):
        user = request.user

        scrap_list = get_object_or_404(ScrapList, id=scrap_list_id)
        if scrap_list.user != user:
            return Response(
                {"message": "본인의 스크랩 리스트만 사용할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if type == "note":
            # 노트 보관

            sn = ScrapNotes.objects.filter(scrap_list=scrap_list, content_id=content_id)
            if sn.exists():
                # 이미 존재하면 삭제
                sn.delete()
                return Response(
                    {"message": "노트를 스크랩 리스트에서 제거했습니다."},
                    status=status.HTTP_200_OK,
                )

            note = get_object_or_404(Notes, id=content_id)
            # ScrapNotes 객체 생성
            ScrapNotes.objects.create(scrap_list=scrap_list, content_id=note.id)
            return Response(
                {
                    "message": f"노트 '{note.song_title}'을(를) '{scrap_list.name}'에 보관 완료"
                },
                status=status.HTTP_201_CREATED,
            )

        elif type == "pli":
            # 플리 보관
            sp = ScrapPlaylists.objects.filter(
                scrap_list=scrap_list, content_id=content_id
            )
            if sp.exists():
                sp.delete()
                return Response(
                    {"message": "플레이리스트를 스크랩 리스트에서 제거했습니다."},
                    status=status.HTTP_200_OK,
                )

            pli = get_object_or_404(Plis, id=content_id)
            # ScrapPlaylists 객체 생성
            ScrapPlaylists.objects.create(scrap_list=scrap_list, content_id=pli.id)
            return Response(
                {
                    "message": f"플리 '{pli.title}'을(를) '{scrap_list.name}'에 보관 완료"
                },
                status=status.HTTP_201_CREATED,
            )

        else:
            return Response(
                {"message": "잘못된 type입니다. 'note' 또는 'pli'를 사용해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ScrapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        scrap_lists = ScrapList.objects.filter(user=user)
        scrap_list_data = []

        for scrap_list in scrap_lists:
            scrap_notes = ScrapNotes.objects.filter(scrap_list=scrap_list)
            scrap_playlists = ScrapPlaylists.objects.filter(scrap_list=scrap_list)

            note_ids = scrap_notes.values_list("content_id", flat=True)
            pli_ids = scrap_playlists.values_list("content_id", flat=True)

            notes = Notes.objects.filter(id__in=note_ids)
            plis = Plis.objects.filter(id__in=pli_ids)

            note_count = notes.count()
            pli_count = plis.count()

            # subtitle 동적 생성 (노트 또는 플리가 0개일 경우 표시하지 않음)
            subtitle_parts = []
            if note_count > 0:
                subtitle_parts.append(f"노트 {note_count}")
            if pli_count > 0:
                subtitle_parts.append(f"플리 {pli_count}")
            subtitle = " · ".join(subtitle_parts) if subtitle_parts else None

            # 앨범아트 노트 + 플리노트 순서대로 네개 가져오기 로직 ..
            merged_items = list(scrap_notes) + list(scrap_playlists)
            merged_items.sort(key=lambda x: x.created_at)

            album_arts = []
            for item in merged_items:
                if isinstance(item, ScrapNotes):
                    note = Notes.objects.filter(id=item.content_id).first()
                    if note and note.album_art:
                        album_arts.append(note.album_art)

                elif isinstance(item, ScrapPlaylists):
                    pli = Plis.objects.filter(id=item.content_id).first()
                    if pli:
                        pli_notes = PliNotes.objects.filter(plis=pli).order_by("created_at")
                        for pn in pli_notes:
                            if pn.notes.album_art:
                                album_arts.append(pn.notes.album_art)
                            if len(album_arts) >= 4:
                                break

                if len(album_arts) >= 4:
                    break

            # 보관함 정보
            scrap_list_info = {
                "id": scrap_list.id,
                "name": scrap_list.name,
                "album_art": album_arts,  # 최대 4개의 앨범 아트를 저장할 리스트
                "subtitle": subtitle,
                "note_count":note_count,
                "pli_count":pli_count
            }

            # 최종적으로 보관함 데이터를 리스트에 추가
            scrap_list_data.append(scrap_list_info)

        return Response(
            {"message": "보관함 조회 성공", "data": scrap_list_data},
            status=status.HTTP_200_OK,
        )


""" class ScrapListCheckView(BlockFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, type, content_id):
        user = request.user

        # 사용자 스크랩 리스트 조회
        scrap_lists = ScrapList.objects.filter(user=user)

        # 반환할 데이터
        scrap_list_data = []

        for scrap_list in scrap_lists:
            # 노트/플리 스크랩 원본 ID 목록 추출
            note_ids = ScrapNotes.objects.filter(scrap_list=scrap_list).values_list(
                "content_id", flat=True
            )
            pli_ids = ScrapPlaylists.objects.filter(scrap_list=scrap_list).values_list(
                "content_id", flat=True
            )

            # Notes, Plis에서 차단 필터 적용
            filtered_notes = self.filter_blocked(
                Notes.objects.filter(id__in=note_ids), user
            )
            filtered_plis = self.filter_blocked(
                Plis.objects.filter(id__in=pli_ids), user
            )

            # 노트 제목과 가수 구성
            note_count = filtered_notes.count()
            pli_count = filtered_plis.count()

            # subtitle 동적 생성 (노트 또는 플리가 0개일 경우 표시하지 않음)
            subtitle_parts = []
            if note_count > 0:
                subtitle_parts.append(f"노트 {note_count}")
            if pli_count > 0:
                subtitle_parts.append(f"플리 {pli_count}")
            subtitle = " · ".join(subtitle_parts) if subtitle_parts else None

            # 최대 4개의 앨범 아트 가져오기
            album_arts = []

            for note in filtered_notes:
                if note.album_art:
                    album_arts.append(note.album_art)
                if len(album_arts) >= 4:
                    break

            # collect 여부 확인
            if type == "note":
                is_collected = ScrapNotes.objects.filter(
                    scrap_list=scrap_list, content_id=content_id
                ).exists()
            elif type == "pli":
                is_collected = ScrapPlaylists.objects.filter(
                    scrap_list=scrap_list, content_id=content_id
                ).exists()
            else:
                return Response(
                    {
                        "message": "유효하지 않은 type입니다. 'note' 또는 'pli'만 가능합니다."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 보관함 정보
            scrap_list_info = {
                "id": scrap_list.id,
                "name": scrap_list.name,
                "album_art": album_arts,  # 최대 4개의 앨범 아트를 저장할 리스트
                "subtitle": subtitle,
                "collect": is_collected,
            }

            # 최종적으로 보관함 데이터를 리스트에 추가
            scrap_list_data.append(scrap_list_info)

        return Response(
            {"message": "보관함 조회 성공", "data": scrap_list_data},
            status=status.HTTP_200_OK,
        )
 """


class ScrapListCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, type, content_id):
        user = request.user

        # 사용자 스크랩 리스트 조회
        scrap_lists = ScrapList.objects.filter(user=user)

        # 반환할 데이터
        scrap_list_data = []

        for scrap_list in scrap_lists:
            # 노트 스크랩 조회
            scrap_notes = ScrapNotes.objects.filter(scrap_list=scrap_list)
            scrap_playlists = ScrapPlaylists.objects.filter(scrap_list=scrap_list)

            note_ids = scrap_notes.values_list("content_id", flat=True)
            pli_ids = scrap_playlists.values_list("content_id", flat=True)

            notes = Notes.objects.filter(id__in=note_ids)
            plis = Plis.objects.filter(id__in=pli_ids)

            note_count = notes.count()
            pli_count = plis.count()

            # subtitle 동적 생성 (노트 또는 플리가 0개일 경우 표시하지 않음)
            subtitle_parts = []
            if note_count > 0:
                subtitle_parts.append(f"노트 {note_count}")
            if pli_count > 0:
                subtitle_parts.append(f"플리 {pli_count}")
            subtitle = " · ".join(subtitle_parts) if subtitle_parts else None

            # 앨범아트 노트 + 플리노트 순서대로 네개 가져오기 로직 ..
            merged_items = list(scrap_notes) + list(scrap_playlists)
            merged_items.sort(key=lambda x: x.created_at)

            album_arts = []
            for item in merged_items:
                if isinstance(item, ScrapNotes):
                    note = Notes.objects.filter(id=item.content_id).first()
                    if note and note.album_art:
                        album_arts.append(note.album_art)

                elif isinstance(item, ScrapPlaylists):
                    pli = Plis.objects.filter(id=item.content_id).first()
                    if pli:
                        pli_notes = PliNotes.objects.filter(plis=pli).order_by("created_at")
                        for pn in pli_notes:
                            if pn.notes.album_art:
                                album_arts.append(pn.notes.album_art)
                            if len(album_arts) >= 4:
                                break

                if len(album_arts) >= 4:
                    break

            # collect 여부 확인
            if type == "note":
                is_collected = ScrapNotes.objects.filter(
                    scrap_list=scrap_list, content_id=content_id
                ).exists()
            elif type == "pli":
                is_collected = ScrapPlaylists.objects.filter(
                    scrap_list=scrap_list, content_id=content_id
                ).exists()
            else:
                return Response(
                    {
                        "message": "유효하지 않은 type입니다. 'note' 또는 'pli'만 가능합니다."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 보관함 정보
            scrap_list_info = {
                "id": scrap_list.id,
                "name": scrap_list.name,
                "album_art": album_arts,  # 최대 4개의 앨범 아트를 저장할 리스트
                "subtitle": subtitle,
                "note_count":note_count,
                "pli_count":pli_count,
                "collect": is_collected,
            }

            # 최종적으로 보관함 데이터를 리스트에 추가
            scrap_list_data.append(scrap_list_info)

        return Response(
            {"message": "보관함 조회 성공", "data": scrap_list_data},
            status=status.HTTP_200_OK,
        )


class ScrapListDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 특정 보관함 상세 조회
    def get(self, request, scrap_list_id):

        user = request.user
        scrap_list = get_object_or_404(ScrapList, id=scrap_list_id)

        if scrap_list.user != user:
            return Response(
                {"error": "본인의 보관함만 조회할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 스크랩된 노트 & 플리 가져오기
        scrap_notes = ScrapNotes.objects.filter(scrap_list=scrap_list)
        scrap_playlists = ScrapPlaylists.objects.filter(scrap_list=scrap_list)

        note_ids = scrap_notes.values_list("content_id", flat=True)
        pli_ids = scrap_playlists.values_list("content_id", flat=True)

        notes = Notes.objects.filter(id__in=note_ids)
        plis = Plis.objects.filter(id__in=pli_ids)

        # 앨범 아트 4개까지 추출 (노트 기준)
        album_arts = list(notes.values_list("album_art", flat=True)[:4])

        # 정보 (노트 개수 + 플리 개수)
        info = [] 
        if notes.count():
            info.append(f"노트 {notes.count()}")
        if plis.count():
            info.append(f"플리 {plis.count()}")

        # 콘텐츠 리스트 구성 (노트 + 플리 직렬화)
        contents = list(NoteSerializer(notes, many=True).data) + list(
            PliSerializer(plis, many=True).data
        )

        return Response(
            {
                "message": "보관함 상세 조회 성공",
                "data": {
                    "name": scrap_list.name,
                    "album_art": album_arts,
                    "info": " · ".join(info),
                    "contents": contents,
                },
            },
            status=status.HTTP_200_OK,
        )


class ScrapListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # 새로운 보관함 생성
    def post(self, request):
        user = request.user
        name = request.data.get("name", "").strip()

        if not name:
            return Response(
                {"error": "보관함 이름을 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 보관함 생성
        scrap_list = ScrapList.objects.create(user=user, name=name)

        return Response(
            {
                "message": "보관함이 생성되었습니다.",
                "data": {"id": scrap_list.id, "name": scrap_list.name},
            },
            status=status.HTTP_201_CREATED,
        )


class ScrapListEditView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, scrap_list_id):
        user = request.user
        scrap_list = get_object_or_404(ScrapList, id=scrap_list_id)

        if scrap_list.user != user:
            return Response(
                {"error": "본인의 보관함만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 보관함 이름 수정
        name = request.data.get("name", "").strip()
        if name:
            scrap_list.name = name
            scrap_list.save()

        # 삭제할 노트 & 플리 가져오기
        remove_notes = request.data.get("remove_notes", [])
        print(remove_notes)
        remove_plis = request.data.get("remove_plis", [])

        # 스크랩된 노트 삭제
        if remove_notes:
            ScrapNotes.objects.filter(
                scrap_list=scrap_list, content_id__in=remove_notes
            ).delete()

        # 스크랩된 플리 삭제
        if remove_plis:
            ScrapPlaylists.objects.filter(
                scrap_list=scrap_list, content_id__in=remove_plis
            ).delete()

        return Response(
            {
                "message": "보관함이 수정되었습니다.",
                "data": {"id": scrap_list.id, "name": scrap_list.name},
            },
            status=status.HTTP_200_OK,
        )

# 보관함 삭제 
class ScrapListDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, content_id):
        user = request.user
        scrap_list = get_object_or_404(ScrapList, id=content_id)

        # 본인 소유 여부 확인
        if scrap_list.user != user:
            return Response(
                {"message": "본인의 보관함만 삭제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = scrap_list.name
        scrap_list.delete() 

        return Response(
            {"message": f"보관함 '{name}' 및 그 안의 노트/플리가 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )