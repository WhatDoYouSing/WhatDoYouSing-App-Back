from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notes.models import *
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import *


class CollectView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, type, scrap_list_id, content_id):
        user = request.user

        scrap_list = get_object_or_404(ScrapList, id=scrap_list_id)
        if scrap_list.user != user:
            return Response({
                "message": "본인의 스크랩 리스트만 사용할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)

        if type == 'note':
            # 노트 보관

            if ScrapNotes.objects.filter(scrap_list=scrap_list, content_id=content_id).exists():
                return Response({
                    "message": "이 노트는 이미 보관되었습니다."
                }, status=status.HTTP_409_CONFLICT)  # 이미 존재하는 경우

            note = get_object_or_404(Notes, id=content_id)
            # ScrapNotes 객체 생성
            scrap_note = ScrapNotes.objects.create(
                scrap_list=scrap_list,
                content_id=note.id
            )
            return Response({
                "message": f"노트 '{note.song_title}'을(를) '{scrap_list.name}'에 보관 완료"
            }, status=status.HTTP_201_CREATED)
       
        elif type == 'pli':
            # 플리 보관
            if ScrapPlaylists.objects.filter(scrap_list=scrap_list, content_id=content_id).exists():
                return Response({
                    "message": "이 플리는 이미 보관되었습니다."
                }, status=status.HTTP_409_CONFLICT)  # 이미 존재하는 경우

            pli = get_object_or_404(Plis, id=content_id)
            # ScrapPlaylists 객체 생성
            scrap_pli = ScrapPlaylists.objects.create(
                scrap_list=scrap_list,
                content_id=pli.id
            )
            return Response({
                "message": f"플리 '{pli.title}'을(를) '{scrap_list.name}'에 보관 완료"
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                "message": "잘못된 type입니다. 'note' 또는 'pli'를 사용해 주세요."
            }, status=status.HTTP_400_BAD_REQUEST)

class ScrapListView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user

        # 사용자 스크랩 리스트 조회
        scrap_lists = ScrapList.objects.filter(user=user)

        # 반환할 데이터
        scrap_list_data = []

        for scrap_list in scrap_lists:
            # 노트 스크랩 조회
            scrap_notes = ScrapNotes.objects.filter(scrap_list=scrap_list)
            scrap_playlists = ScrapPlaylists.objects.filter(scrap_list=scrap_list)

            # 노트 제목과 가수 구성
            note_count = scrap_notes.count()
            pli_count = scrap_playlists.count()

            # subtitle 동적 생성 (노트 또는 플리가 0개일 경우 표시하지 않음)
            subtitle_parts = []
            if note_count > 0:
                subtitle_parts.append(f"노트 {note_count}")
            if pli_count > 0:
                subtitle_parts.append(f"플리 {pli_count}")
            subtitle = " · ".join(subtitle_parts) if subtitle_parts else None

            # 최대 4개의 앨범 아트 가져오기
            album_arts = []
            note_ids = scrap_notes.values_list('content_id', flat=True)  # content_id 가져오기
            notes = Notes.objects.filter(id__in=note_ids)  # Notes에서 조회

            for note in notes:
                if note.album_art:
                    album_arts.append(note.album_art)
                if len(album_arts) >= 4:  # 최대 4개까지만
                    break

            # 보관함 정보
            scrap_list_info = {
                "id": scrap_list.id,
                "name": scrap_list.name,
                "album_art": album_arts,  # 최대 4개의 앨범 아트를 저장할 리스트
                "subtitle": subtitle
            }

            # 최종적으로 보관함 데이터를 리스트에 추가
            scrap_list_data.append(scrap_list_info)

        return Response({
            "message": "보관함 조회 성공",
            "data": scrap_list_data
        }, status=status.HTTP_200_OK)