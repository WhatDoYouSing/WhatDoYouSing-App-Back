from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import Q
from accounts.models import User
from notes.models import *
from .serializers import *


# 통합검색(노트)
class SearchNotesView(views.APIView):
    def get(self, request):
        keyword = request.GET.get("keyword", "").strip()  # strip으로 공백 제거
        writer = request.GET.get("writer", "").strip()  # strip으로 공백 제거
        totaltag = request.GET.getlist("totaltag")  # 여러 개 태그 검색 가능
        filter_type = request.GET.get("filter", "").strip()  # default: 전체 검색

        if not filter_type:  # 빈 문자열일 경우 전체 결과 반환
            filter_type = "all"

        valid_filters = ["all", "Memo", "Lyrics", "Title", "Singer", "Location"]
        if filter_type not in valid_filters:
            return Response(
                {
                    "message": "잘못된 필터 값입니다. 허용된 필터: all, Memo, Lyrics, Title, Singer, Location"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = Q()
        user_query = None

        # 1. 사용자 검색 필터 적용 (@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    user_query = Q(user=user)
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif writer.startswith("@"):
                username_or_nickname = writer.replace(
                    "@", ""
                ).strip()  # `@닉네임` → 닉네임 또는 아이디 추출
                try:
                    user = User.objects.get(
                        Q(username=username_or_nickname)
                        | Q(nickname=username_or_nickname)
                    )
                    user_query = Q(
                        user=user
                    )  # ✅ ID(username) 또는 닉네임(nickname) 검색
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # 2. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag:
            # '2,3' → ['2', '3'] 리스트로 변환
            totaltag = totaltag[0].split(",") if len(totaltag) == 1 else totaltag

            for tag in totaltag:
                query &= (
                    Q(emotion__name=tag)
                    | Q(tag_time__name__in=[tag])
                    | Q(tag_season__name__in=[tag])
                    | Q(tag_context__name__in=[tag])
                )

        # 3. 키워드 검색 적용 (사용자 검색이 아닐 경우)
        if keyword:
            keyword_filter = (
                Q(memo__icontains=keyword)
                | Q(lyrics__icontains=keyword)
                | Q(song_title__icontains=keyword)
                | Q(artist__icontains=keyword)
                | Q(location_name__icontains=keyword)
                | Q(location_address__icontains=keyword)
            )
            query &= keyword_filter  # ✅ 기존 조건과 AND 결합

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            query &= user_query

        # ✅ 검색 실행
        search_results = Notes.objects.filter(query).distinct()

        # ✅ keyword가 있을 경우에만 필터 적용
        data = {
            "Memo": SearchNotesMemoSerializer(
                (
                    search_results.filter(memo__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Lyrics": SearchNotesLTSSerializer(
                (
                    search_results.filter(lyrics__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Title": SearchNotesLTSSerializer(
                (
                    search_results.filter(song_title__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Singer": SearchNotesLTSSerializer(
                (
                    search_results.filter(artist__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Location": SearchNotesLocationSerializer(
                search_results.filter(
                    (
                        Q(location_name__icontains=keyword)
                        | Q(location_address__icontains=keyword)
                    )
                    if keyword
                    else Q()
                ),
                many=True,
            ).data,
        }

        # ✅ 특정 필터가 있는 경우 해당 데이터만 반환
        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 노트 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )


# 통합검색(플리)
class SearchPlisView(views.APIView):
    def get(self, request):
        keyword = request.GET.get("keyword", "").strip()  # strip으로 공백 제거
        writer = request.GET.get("writer", "").strip()  # strip으로 공백 제거
        totaltag = request.GET.getlist("totaltag")  # 여러 개 태그 검색 가능
        filter_type = request.GET.get("filter", "").strip()  # default: 전체 검색

        if not filter_type:  # 빈 문자열일 경우 전체 결과 반환
            filter_type = "all"

        valid_filters = ["all", "Memo", "Lyrics", "SongTitle", "Singer", "PlisTitle"]
        if filter_type not in valid_filters:
            return Response(
                {
                    "message": "잘못된 필터 값입니다. 허용된 필터: all, Memo, Lyrics, SongTitle, Singer, PlisTitle"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = Q()
        user_query = None

        # 1. 사용자 검색 필터 적용 (@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    user_query = Q(user=user)
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif writer.startswith("@"):
                username_or_nickname = writer.replace(
                    "@", ""
                ).strip()  # `@닉네임` → 닉네임 또는 아이디 추출
                try:
                    user = User.objects.get(
                        Q(username=username_or_nickname)
                        | Q(nickname=username_or_nickname)
                    )
                    user_query = Q(
                        user=user
                    )  # ✅ ID(username) 또는 닉네임(nickname) 검색
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # 2. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag:
            # '2,3' → ['2', '3'] 리스트로 변환
            totaltag = totaltag[0].split(",") if len(totaltag) == 1 else totaltag

            tag_queries = []
            for tag in totaltag:
                tag_queries.append(
                    Q(tag_time__name=tag)
                    | Q(tag_season__name=tag)
                    | Q(tag_context__name=tag)
                )

            if tag_queries:
                query &= Q(*tag_queries, _connector=Q.AND)
            """
            for tag in totaltag:
                query &= (
                    Q(tag_time__name__in=[tag])
                    | Q(tag_season__name__in=[tag])
                    | Q(tag_context__name__in=[tag])
                )
            """

        # 3. 키워드 검색 적용 (사용자 검색이 아닐 경우)
        if keyword:
            keyword_filter = (
                Q(plinotes__note_memo__icontains=keyword)  # 플리 메모(PliNotes)
                | Q(plinotes__notes__lyrics__icontains=keyword)  # 가사(Notes)
                | Q(plinotes__notes__song_title__icontains=keyword)  # 곡명(Notes)
                | Q(plinotes__notes__artist__icontains=keyword)  # 가수(Notes)
                | Q(title__icontains=keyword)  # 플리 제목(Plis)
            )
            query &= keyword_filter  # ✅ 기존 조건과 AND 결합

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            query &= user_query

        # ✅ 검색 실행
        search_results = Plis.objects.filter(query).distinct()

        # ✅ keyword가 있을 경우에만 필터 적용
        data = {
            "Memo": SearchPlisMemoSerializer(
                (
                    search_results.filter(plinotes__note_memo__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Lyrics": SearchPlisLSSPSerializer(
                (
                    search_results.filter(plinotes__notes__lyrics__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "SongTitle": SearchPlisLSSPSerializer(
                (
                    search_results.filter(
                        plinotes__notes__song_title__icontains=keyword
                    )
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Singer": SearchPlisLSSPSerializer(
                (
                    search_results.filter(plinotes__notes__artist__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "PlisTitle": SearchPlisLSSPSerializer(
                (
                    search_results.filter(title__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
        }

        # ✅ 특정 필터가 있는 경우 해당 데이터만 반환
        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 플리 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )


# 통합검색(작성자)
class SearchWritersView(views.APIView):
    def get(self, request):
        keyword = request.GET.get("keyword", "").strip()  # strip으로 공백 제거
        writer = request.GET.get("writer", "").strip()  # strip으로 공백 제거

        query = Q()
        user_query = None

        if not writer and not keyword:
            return Response(
                {
                    "message": "탐색결과 작성자 조회 성공",
                    "data": {"user": []},  # 빈 리스트 반환
                },
                status=status.HTTP_200_OK,
            )

        # 1. 사용자 검색 필터 적용 (@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    user_query = Q(id=user.id)
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif writer.startswith("@"):
                username_or_nickname = writer.replace(
                    "@", ""
                ).strip()  # `@닉네임` → 닉네임 또는 아이디 추출
                try:
                    user = User.objects.get(
                        Q(username=username_or_nickname)
                        | Q(nickname=username_or_nickname)
                    )
                    user_query = Q(
                        id=user.id
                    )  # ID(username) 또는 닉네임(nickname) 검색
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # 2. 키워드 검색 적용 (사용자 검색이 아닐 경우)
        if keyword:
            keyword_filter = Q(nickname__icontains=keyword)  # 닉네임으로 작성자 검색색
            query &= keyword_filter  # ✅ 기존 조건과 AND 결합

        # 3. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            query &= user_query

        # ✅ 검색 실행
        search_results = User.objects.filter(query).distinct()

        return Response(
            {
                "message": "탐색결과 작성자 조회 성공",
                "data": {
                    "user": SearchWritersSerializer(search_results, many=True).data
                },
            },
            status=status.HTTP_200_OK,
        )
