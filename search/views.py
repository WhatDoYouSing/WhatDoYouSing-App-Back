from itertools import chain
from django.db.models import Value, CharField
from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import Exists, OuterRef, Value, BooleanField, Q
from social.models import UserFollows
from accounts.models import User
from notes.models import *
from .serializers import *


# 통합검색(전체)
class SearchView(views.APIView):
    def get(self, request):
        keyword = request.GET.get("keyword", "").strip()  # strip으로 공백 제거
        writer = request.GET.get("writer", "").strip()  # strip으로 공백 제거
        totaltag = request.GET.getlist("totaltag")  # 여러 개 태그 검색 가능
        filter_type = request.GET.get("filter", "").strip()  # default: 전체 검색

        if not filter_type:  # 빈 문자열일 경우 전체 결과 반환
            filter_type = "all"

        valid_filters = [
            "all",
            "Memo",
            "Lyrics",
            "SongTitle",
            "Singer",
            "Location",
            "PlisTitle",
        ]
        if filter_type not in valid_filters:
            return Response(
                {
                    "message": "잘못된 필터 값입니다. 허용된 필터: all, Memo, Lyrics, SongTitle, Singer, Location, PliTitle"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        note_query = Q()
        plis_query = Q()
        user_query = None
        has_filter = False

        # 1. 사용자 검색 필터 적용 (@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    user_query = Q(user=user)
                    has_filter = True
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
                    has_filter = True
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # 2. 키워드 검색 적용 (사용자 검색이 아닐 경우)
        # 노트+플리: 메모,곡명,가수명/노트만: 가사,위치/플리만:플리제목목
        if keyword:
            note_keyword_filter = Q()
            plis_keyword_filter = Q()

            note_keyword_filter = (
                Q(memo__icontains=keyword)
                | Q(lyrics__icontains=keyword)
                | Q(song_title__icontains=keyword)
                | Q(artist__icontains=keyword)
                | Q(location_name__icontains=keyword)
                | Q(location_address__icontains=keyword)
            )
            note_query &= note_keyword_filter

            plis_keyword_filter = (
                Q(plinotes__note_memo__icontains=keyword)
                | Q(plinotes__notes__lyrics__icontains=keyword)
                | Q(plinotes__notes__song_title__icontains=keyword)
                | Q(plinotes__notes__artist__icontains=keyword)
                | Q(title__icontains=keyword)
            )
            plis_query &= plis_keyword_filter
            has_filter = True
        """
        # 3. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag:
            # 쉼표로 구분된 문자열을 개별 태그 ID로 분리하여 리스트를 만듭니다.
            # 예: totaltag=['1,2'] -> totaltag_ids=[1, 2]
            # 예: totaltag=['1', '2'] -> totaltag_ids=[1, 2]
            processed_tag_ids = []
            for tag_str in totaltag:
                # 각 문자열을 쉼표로 분리하고 공백을 제거한 뒤 숫자로 변환합니다.
                for s_id in tag_str.split(","):
                    s_id = s_id.strip()
                    if s_id:  # 빈 문자열이 아닌 경우에만 처리
                        try:
                            processed_tag_ids.append(int(s_id))
                        except ValueError:
                            return Response(
                                {
                                    "message": f"유효하지 않은 태그 ID입니다: {s_id}. 태그 ID는 숫자여야 합니다."
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            # 중복된 태그 ID를 제거하여 효율성을 높일 수 있습니다.
            totaltag_ids = list(set(processed_tag_ids))

            if not totaltag_ids:  # 처리 후 유효한 태그 ID가 없는 경우
                return Response(
                    {"message": "검색할 유효한 태그 ID가 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Notes에 대한 태그 필터: 각 태그 ID에 대해 OR 조건으로 태그 필드를 검색하고, 이를 전체 note_query에 AND로 연결합니다.
            for tag_id in totaltag_ids:
                note_query &= (
                    Q(emotion__id=tag_id)
                    | Q(tag_time__id=tag_id)
                    | Q(tag_season__id=tag_id)
                    | Q(tag_context__id=tag_id)
                )

            # Plis에 대한 태그 필터: 각 태그 ID에 대해 OR 조건으로 태그 필드를 검색하고, 이를 전체 plis_query에 AND로 연결합니다.
            for tag_id in totaltag_ids:
                plis_query &= (
                    Q(tag_time__id=tag_id)
                    | Q(tag_season__id=tag_id)
                    | Q(tag_context__id=tag_id)
                )
            has_filter = bool(totaltag_ids)
            """
        # 3. 태그 필터 적용 (교집합, name 기준)
        if totaltag:
            # 1) 쉼표/리스트 섞여 온 문자열을 개별 태그 이름으로 분리
            processed_tag_names = []
            for tag_str in totaltag:
                for name in tag_str.split(","):
                    name = name.strip()
                    if name:
                        processed_tag_names.append(name)
            # 중복 제거
            processed_tag_names = list(set(processed_tag_names))

            # 2) 각 태그 이름마다 AND-OR 조건 반복 적용
            for tag_name in processed_tag_names:
                note_query &= (
                    Q(emotion__name=tag_name)
                    | Q(tag_time__name=tag_name)
                    | Q(tag_season__name=tag_name)
                    | Q(tag_context__name=tag_name)
                )
                plis_query &= (
                    Q(tag_time__name=tag_name)
                    | Q(tag_season__name=tag_name)
                    | Q(tag_context__name=tag_name)
                )

            has_filter = bool(processed_tag_names)

        """
        # 3. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag and any(totaltag):
            totaltag = (
                [int(tag) for tag in totaltag[0].split(",")]
                if len(totaltag) == 1
                else list(map(int, totaltag))
            )

            note_tag_filter = Q()
            plis_tag_filter = Q()

            note_tag_filter &= (
                Q(emotion__name__in=totaltag)
                | Q(tag_time__name__in=totaltag)
                | Q(tag_season__name__in=totaltag)
                | Q(tag_context__name__in=totaltag)
            )
            note_query &= note_tag_filter

            plis_tag_filter &= (
                Q(tag_time__name__in=totaltag)
                | Q(tag_season__name__in=totaltag)
                | Q(tag_context__name__in=totaltag)
            )
            plis_query &= plis_tag_filter
            has_filter = True
        """

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            if note_query == Q():
                note_query = user_query  # 다른 필터 조건이 없으면 단독 적용
            else:
                note_query &= user_query

            if plis_query == Q():
                plis_query = user_query
            else:
                plis_query &= user_query
            has_filter = True

        # 검색 실행
        notes_results = (
            Notes.objects.filter(note_query).distinct()
            if has_filter
            else Notes.objects.all()
        )
        plis_results = (
            Plis.objects.filter(plis_query).distinct()
            if has_filter
            else Plis.objects.all()
        )

        # 데이터 직렬화
        data = {
            "Memo": SearchAllMemoNotesSerializer(notes_results, many=True).data
            + SearchAllPlisSerializer(plis_results, many=True).data,
            "Lyrics": SearchAllNotesLSSSerializer(notes_results, many=True).data,
            "SongTitle": SearchAllNotesLSSSerializer(notes_results, many=True).data
            + SearchAllPlisSSPSerializer(plis_results, many=True).data,
            "Singer": SearchAllNotesLSSSerializer(notes_results, many=True).data
            + SearchAllPlisSSPSerializer(plis_results, many=True).data,
            "Location": SearchAllNotesLocationSerializer(notes_results, many=True).data,
            "PlisTitle": SearchAllPlisSSPSerializer(plis_results, many=True).data,
        }

        # ✅ 특정 필터가 있는 경우 해당 데이터만 반환
        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 통합 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )


"""
# 통합검색(전체)
class SearchView(views.APIView):
    def get(self, request):
        keyword = request.GET.get("keyword", "").strip()  # strip으로 공백 제거
        writer = request.GET.get("writer", "").strip()  # strip으로 공백 제거
        totaltag = request.GET.getlist("totaltag")  # 여러 개 태그 검색 가능
        filter_type = request.GET.get("filter", "").strip()  # default: 전체 검색

        if not filter_type:  # 빈 문자열일 경우 전체 결과 반환
            filter_type = "all"

        valid_filters = [
            "all",
            "Memo",
            "Lyrics",
            "SongTitle",
            "Singer",
            "Location",
            "PlisTitle",
        ]
        if filter_type not in valid_filters:
            return Response(
                {
                    "message": "잘못된 필터 값입니다. 허용된 필터: all, Memo, Lyrics, SongTitle, Singer, Location, PliTitle"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        note_query = Q()
        plis_query = Q()
        user_query = None
        has_filter = False

        # 1. 사용자 검색 필터 적용 (@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    user_query = Q(user=user)
                    has_filter = True
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
                    has_filter = True
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # 2. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag:
            totaltag = totaltag[0].split(",") if len(totaltag) == 1 else totaltag
            for tag in totaltag:
                note_query &= (
                    Q(emotion__name=tag)
                    | Q(tag_time__name=[tag])
                    | Q(tag_season__name=[tag])
                    | Q(tag_context__name=[tag])
                )
                plis_query &= (
                    Q(tag_time__name=[tag])
                    | Q(tag_season__name=[tag])
                    | Q(tag_context__name=[tag])
                )
                has_filter = True

        # 3. 키워드 검색 적용 (사용자 검색이 아닐 경우)
        # 노트+플리: 메모,곡명,가수명/노트만: 가사,위치/플리만:플리제목목
        if keyword:
            note_query_filter = (
                Q(memo__icontains=keyword)
                | Q(lyrics__icontains=keyword)
                | Q(song_title__icontains=keyword)
                | Q(artist__icontains=keyword)
                | Q(location_name__icontains=keyword)
                | Q(location_address__icontains=keyword)
            )
            note_query &= note_query_filter

            plis_query_filter = (
                Q(plinotes__note_memo__icontains=keyword)
                | Q(plinotes__notes__lyrics__icontains=keyword)
                | Q(plinotes__notes__song_title__icontains=keyword)
                | Q(plinotes__notes__artist__icontains=keyword)
                | Q(title__icontains=keyword)
            )
            plis_query &= plis_query_filter
            has_filter = True

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            if note_query == Q():
                note_query = user_query  # 다른 필터 조건이 없으면 단독 적용
            else:
                note_query &= user_query

            if plis_query == Q():
                plis_query = user_query
            else:
                plis_query &= user_query
            has_filter = True

        # 검색 실행
        notes_results = (
            Notes.objects.filter(note_query).distinct()
            if has_filter
            else Notes.objects.all()
        )
        plis_results = (
            Plis.objects.filter(plis_query).distinct()
            if has_filter
            else Plis.objects.all()
        )

        # 데이터 직렬화
        data = {
            "Memo": SearchAllMemoNotesSerializer(notes_results, many=True).data
            + SearchAllPlisSerializer(plis_results, many=True).data,
            "Lyrics": SearchAllNotesLSSSerializer(notes_results, many=True).data,
            "SongTitle": SearchAllNotesLSSSerializer(notes_results, many=True).data
            + SearchAllPlisSSPSerializer(plis_results, many=True).data,
            "Singer": SearchAllNotesLSSSerializer(notes_results, many=True).data
            + SearchAllPlisSSPSerializer(plis_results, many=True).data,
            "Location": SearchAllNotesLocationSerializer(notes_results, many=True).data,
            "PlisTitle": SearchAllPlisSSPSerializer(plis_results, many=True).data,
        }

        # ✅ 특정 필터가 있는 경우 해당 데이터만 반환
        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 통합 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )
"""


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
        has_filter = False
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
                    has_filter = True
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
                    has_filter = True
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        """
        # 2. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag and any(totaltag):
            totaltag = (
                [int(tag) for tag in totaltag[0].split(",")]
                if len(totaltag) == 1
                else list(map(int, totaltag))
            )

            query &= (
                Q(emotion__name__in=totaltag)
                | Q(tag_time__name__in=totaltag)
                | Q(tag_season__name__in=totaltag)
                | Q(tag_context__name__in=totaltag)
            )

            has_filter = True
        """
        # 2. 태그 필터 적용 (교집합, name 기준)
        if totaltag:
            # 1) 쉼표/리스트 섞여 온 문자열을 개별 태그 이름으로 분리
            processed_tag_names = []
            for tag_str in totaltag:
                for name in tag_str.split(","):
                    name = name.strip()
                    if name:
                        processed_tag_names.append(name)
            # 중복 제거
            processed_tag_names = list(set(processed_tag_names))

            # 2) 각 태그 이름마다 AND-OR 조건 반복 적용
            for tag_name in processed_tag_names:
                query &= (
                    Q(emotion__name=tag_name)
                    | Q(tag_time__name=tag_name)
                    | Q(tag_season__name=tag_name)
                    | Q(tag_context__name=tag_name)
                )

            has_filter = bool(processed_tag_names)

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
            has_filter = True

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            if query == Q():  # 다른 필터 조건이 없으면 단독 적용
                query = user_query
            else:
                query &= user_query
            has_filter = True

        # ✅ 검색 실행
        search_results = (
            Notes.objects.filter(query).distinct()
            if has_filter
            else Notes.objects.all()
        )

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
        has_filter = False
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
                    has_filter = True
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
                    has_filter = True
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        # 2. 태그 필터 적용 (교집합, name 기준)
        if totaltag:
            # 1) 쉼표/리스트 섞여 온 문자열을 개별 태그 이름으로 분리
            processed_tag_names = []
            for tag_str in totaltag:
                for name in tag_str.split(","):
                    name = name.strip()
                    if name:
                        processed_tag_names.append(name)
            # 중복 제거
            processed_tag_names = list(set(processed_tag_names))

            # 2) 각 태그 이름마다 AND-OR 조건 반복 적용
            for tag_name in processed_tag_names:
                query &= (
                    Q(tag_time__name=tag_name)
                    | Q(tag_season__name=tag_name)
                    | Q(tag_context__name=tag_name)
                )

            has_filter = bool(processed_tag_names)
        """
        # 2. 태그 필터 적용 (교집합, 다중검색 가능)
        if totaltag and any(totaltag):
            totaltag = (
                [int(tag) for tag in totaltag[0].split(",")]
                if len(totaltag) == 1
                else list(map(int, totaltag))
            )

            query &= (
                Q(tag_time__name__in=totaltag)
                | Q(tag_season__name__in=totaltag)
                | Q(tag_context__name__in=totaltag)
            )
            has_filter = True
        """
        """
            tag_queries = []
            for tag in totaltag:
                tag_queries.append(
                    Q(tag_time__name=tag)
                    | Q(tag_season__name=tag)
                    | Q(tag_context__name=tag)
                )

            if tag_queries:
                query &= Q(*tag_queries, _connector=Q.AND)
            has_filter = True
        """
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
            has_filter = True

        # 4. 사용자 검색이 있는 경우, 사용자 필터 적용
        if user_query:
            if query == Q():  # 다른 필터 조건이 없으면 단독 적용
                query = user_query
            else:
                query &= user_query
            has_filter = True

        # ✅ 검색 실행
        search_results = (
            Plis.objects.filter(query).distinct() if has_filter else Plis.objects.all()
        )

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

        # 1. writer와 keyword가 둘 다 존재하는 경우 → 검색 불가능 (빈 리스트 반환)
        if writer and keyword:
            return Response(
                {
                    "message": "writer과 keyword 함께 검색 시 검색 결과 뜨지 않습니다.",
                    "data": {"user": []},  # 빈 리스트 반환
                },
                status=status.HTTP_200_OK,
            )
        query = Q()

        # 2. writer 검색(@닉네임, @아이디, from:@아이디)
        if writer:
            if writer.startswith("from:@"):
                username = writer.replace(
                    "from:@", ""
                ).strip()  # `from:@아이디` → 아이디만 추출
                try:
                    user = User.objects.get(username=username)  # ✅ ID(username)만 검색
                    query = Q(id=user.id)
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
                    query = Q(id=user.id)  # ID(username) 또는 닉네임(nickname) 검색
                except User.DoesNotExist:
                    return Response(
                        {"message": "해당 사용자가 존재하지 않습니다."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {
                        "message": "잘못된 writer 형식입니다. @닉네임 또는 from:@아이디만 가능합니다."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 3. 키워드 검색 (사용자 검색이 아닐 경우)
        elif keyword:
            query = Q(nickname__icontains=keyword)

        else:
            return Response(
                {
                    "message": "탐색결과 작성자 조회 성공",
                    "data": {"user": []},  # 빈 리스트 반환
                },
                status=status.HTTP_200_OK,
            )

        # 검색 실행
        qs = User.objects.filter(query).distinct()

        # 4. 로그인 여부에 따라 annotate
        me = request.user
        if me.is_authenticated:
            qs = qs.annotate(
                is_following=Exists(
                    UserFollows.objects.filter(follower=me, following=OuterRef("pk"))
                ),
                is_follower=Exists(
                    UserFollows.objects.filter(follower=OuterRef("pk"), following=me)
                ),
            )
        else:
            # 비로그인 시 항상 False
            qs = qs.annotate(
                is_following=Value(False, output_field=BooleanField()),
                is_follower=Value(False, output_field=BooleanField()),
            )

        serializer = SearchWritersSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(
            {"message": "탐색결과 작성자 조회 성공", "data": {"user": serializer.data}},
            status=status.HTTP_200_OK,
        )
