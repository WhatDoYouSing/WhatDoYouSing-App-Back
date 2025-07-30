from itertools import chain
from django.db.models import Value, CharField
from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import Exists, OuterRef, Value, BooleanField, Q
from social.models import UserFollows
from accounts.models import User
from notes.models import *
from moderation.models import *
from .serializers import *
from moderation.mixins import BlockFilterMixin
from moderation.utils.blocking import blocked_user_ids


# ────────────────────────────────────────────────────────────
# 통합검색(전체)
# ────────────────────────────────────────────────────────────
""" class SearchView(BlockFilterMixin, views.APIView):
    
    # keyword  : 메모/가사/곡명/가수/플리제목·위치 등 텍스트 검색
    # writer   : @닉네임, @아이디, from:@아이디
    # totaltag : 태그 이름 리스트(쉼표 가능)
    # filter   : all | Memo | Lyrics | SongTitle | ...
    

    def get(self, request):
        # ── 0. 기본 파라미터 ───────────────────────────
        keyword = request.GET.get("keyword", "").strip()
        writer = request.GET.get("writer", "").strip()
        totaltag = request.GET.getlist("totaltag")
        filter_type = request.GET.get("filter", "").strip() or "all"

        valid_filters = {
            "all",
            "Memo",
            "Lyrics",
            "SongTitle",
            "Singer",
            "Location",
            "PlisTitle",
        }
        if filter_type not in valid_filters:
            return Response(
                {"message": "filter 값이 유효하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 1. 쿼리 객체 준비 ───────────────────────────
        note_q = Q()
        pli_q = Q()
        user_q = None
        has_cond = False

        # ── 1-A. 작성자 필터 (@닉 / from:@) ───────────────
        if writer:
            if writer.startswith("from:@"):
                u_name = writer[6:].strip()
                user_q = Q(user__username=u_name)
            elif writer.startswith("@"):
                name = writer[1:].strip()
                user_q = Q(user__username=name) | Q(user__nickname=name)
            else:
                return Response(
                    {
                        "message": "writer 형식은 @닉네임 또는 from:@아이디만 가능합니다."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            has_cond = True

        # ── 1-B. 키워드 필터 ───────────────────────────
        if keyword:
            note_q &= (
                Q(memo__icontains=keyword)
                | Q(lyrics__icontains=keyword)
                | Q(song_title__icontains=keyword)
                | Q(artist__icontains=keyword)
                | Q(location_name__icontains=keyword)
                | Q(location_address__icontains=keyword)
            )
            pli_q &= (
                Q(plinotes__note_memo__icontains=keyword)
                | Q(plinotes__notes__lyrics__icontains=keyword)
                | Q(plinotes__notes__song_title__icontains=keyword)
                | Q(plinotes__notes__artist__icontains=keyword)
                | Q(title__icontains=keyword)
            )
            has_cond = True

        # ── 1-C. 태그 필터(이름 기준, 교집합) ─────────────
        if totaltag:
            names = {n.strip() for tag in totaltag for n in tag.split(",") if n.strip()}
            for n in names:
                note_q &= (
                    Q(emotion__name=n)
                    | Q(tag_time__name=n)
                    | Q(tag_season__name=n)
                    | Q(tag_context__name=n)
                )
                pli_q &= (
                    Q(tag_time__name=n) | Q(tag_season__name=n) | Q(tag_context__name=n)
                )
            if names:
                has_cond = True

        # ── 1-D. 작성자 조건 합치기 ──────────────────────
        if user_q:
            note_q &= user_q
            pli_q &= user_q

        # ── 2. QuerySet 생성 ───────────────────────────
        notes_qs = (
            Notes.objects.filter(note_q).distinct() if has_cond else Notes.objects.all()
        )
        plis_qs = (
            Plis.objects.filter(pli_q).distinct() if has_cond else Plis.objects.all()
        )

        # ── 3. 차단 필터 ───────────────────────────────
        self.block_model = Notes
        notes_qs = self.filter_blocked(notes_qs)
        self.block_model = Plis
        plis_qs = self.filter_blocked(plis_qs)
        self.block_model = None  # 사이드이펙트 방지

        # ── 4. visibility + 팔로우 annotate ────────────
        me = request.user
        if me.is_authenticated:
            # 서로 맞팔 여부
            for qs in (notes_qs, plis_qs):
                qs = qs.annotate(
                    is_following=Exists(
                        UserFollows.objects.filter(
                            follower=me, following=OuterRef("user_id")
                        )
                    ),
                    is_follower=Exists(
                        UserFollows.objects.filter(
                            follower=OuterRef("user_id"), following=me
                        )
                    ),
                )

            following = UserFollows.objects.filter(follower=me).values_list(
                "following_id", flat=True
            )
            vis_note_q = (
                Q(visibility="public")
                | Q(user=me)
                | Q(
                    visibility="friends",
                    user__in=following,
                    user__follower_set__follower=me,
                )
            )
            vis_pli_q = vis_note_q

            notes_qs = notes_qs.filter(vis_note_q)
            plis_qs = plis_qs.filter(vis_pli_q)
        else:
            notes_qs = notes_qs.filter(visibility="public")
            plis_qs = plis_qs.filter(visibility="public")

        # ── 5. 직렬화 그룹핑 (필터 경로만 교정) ───────────────────
        data = {
            # ① Memo  ─ notes.memo / plinotes.note_memo
            "Memo": SearchAllMemoNotesSerializer(
                (notes_qs.filter(memo__icontains=keyword) if keyword else notes_qs),
                many=True,
            ).data
            + SearchAllPlisSerializer(
                (
                    plis_qs.filter(plinotes__note_memo__icontains=keyword)
                    if keyword
                    else plis_qs
                ),
                many=True,
            ).data,
            # ② Lyrics ─ notes.lyrics / plinotes.notes.lyrics
            "Lyrics": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(lyrics__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data,
            # ③ SongTitle ─ notes.song_title / plinotes.notes.song_title
            "SongTitle": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(song_title__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data
            + SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(plinotes__notes__song_title__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
            # ④ Singer ─ notes.artist / plinotes.notes.artist
            "Singer": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(artist__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data
            + SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(plinotes__notes__artist__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
            # ⑤ Location ─ notes.location_name/address (플리엔 없음)
            "Location": SearchAllNotesLocationSerializer(
                (
                    notes_qs.filter(
                        Q(location_name__icontains=keyword)
                        | Q(location_address__icontains=keyword)
                    )
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data,
            # ⑥ PlisTitle ─ 플리 자체 제목 (노트엔 해당 없음)
            "PlisTitle": SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(title__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
        }

        result = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 통합 조회 성공", "data": result},
            status=status.HTTP_200_OK,
        )
 """


class SearchView(BlockFilterMixin, views.APIView):
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

        # === (1) 기본 QuerySet 준비 ===
        notes_qs = Notes.objects.none()
        plis_qs = Plis.objects.none()

        if has_filter:
            notes_qs = Notes.objects.filter(note_query).distinct()
            plis_qs = Plis.objects.filter(plis_query).distinct()
        else:
            notes_qs = Notes.objects.all()
            plis_qs = Plis.objects.all()

        # notes_qs = (
        #     Notes.objects.filter(note_query).distinct()
        #     if has_filter
        #     else Notes.objects.all()
        # )
        # plis_qs = (
        #     Plis.objects.filter(plis_query).distinct()
        #     if has_filter
        #     else Plis.objects.all()
        # )

        # ────────────────────────────────────────────────
        # ★★ 차단된 게시글·작성자 필터링 추가 ★★
        # ────────────────────────────────────────────────
        self.block_model = Notes  # ▶ 노트용으로 설정
        notes_qs = self.filter_blocked(notes_qs)
        self.block_model = Plis  # ▶ 플리용으로 재설정
        plis_qs = self.filter_blocked(plis_qs)

        self.block_model = None

        me = request.user
        if me.is_authenticated:
            # === (2) 맞팔 여부 annotate ===
            notes_qs = notes_qs.annotate(
                is_following=Exists(
                    UserFollows.objects.filter(
                        follower=me, following=OuterRef("user_id")
                    )
                ),
                is_follower=Exists(
                    UserFollows.objects.filter(
                        follower=OuterRef("user_id"), following=me
                    )
                ),
            )
            plis_qs = plis_qs.annotate(
                is_following=Exists(
                    UserFollows.objects.filter(
                        follower=me, following=OuterRef("user_id")
                    )
                ),
                is_follower=Exists(
                    UserFollows.objects.filter(
                        follower=OuterRef("user_id"), following=me
                    )
                ),
            )

            # === (3) visibility 필터 ===
            note_vis_q = (
                Q(visibility="public")
                | Q(visibility="private", user=me)
                | Q(visibility="friends", is_following=True, is_follower=True)
            )
            plis_vis_q = (
                Q(visibility="public")
                | Q(visibility="private", user=me)
                | Q(visibility="friends", is_following=True, is_follower=True)
            )

            notes_results = notes_qs.filter(note_vis_q)
            plis_results = plis_qs.filter(plis_vis_q)
        else:
            # 비로그인: public 만
            notes_results = notes_qs.filter(visibility="public")
            plis_results = plis_qs.filter(visibility="public")

        """ # === (4) 직렬화 및 응답 (기존 코드 그대로) ===
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
        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 통합 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        ) """
        data = {
            # ① Memo  ─ notes.memo / plinotes.note_memo
            "Memo": SearchAllMemoNotesSerializer(
                (notes_qs.filter(memo__icontains=keyword) if keyword else notes_qs),
                many=True,
            ).data
            + SearchAllPlisSerializer(
                (
                    plis_qs.filter(plinotes__note_memo__icontains=keyword)
                    if keyword
                    else plis_qs
                ),
                many=True,
            ).data,
            # ② Lyrics ─ notes.lyrics / plinotes.notes.lyrics
            "Lyrics": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(lyrics__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data,
            # ③ SongTitle ─ notes.song_title / plinotes.notes.song_title
            "SongTitle": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(song_title__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data
            + SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(plinotes__notes__song_title__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
            # ④ Singer ─ notes.artist / plinotes.notes.artist
            "Singer": SearchAllNotesLSSSerializer(
                (
                    notes_qs.filter(artist__icontains=keyword)
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data
            + SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(plinotes__notes__artist__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
            # ⑤ Location ─ notes.location_name/address (플리엔 없음)
            "Location": SearchAllNotesLocationSerializer(
                (
                    notes_qs.filter(
                        Q(location_name__icontains=keyword)
                        | Q(location_address__icontains=keyword)
                    )
                    if keyword
                    else notes_qs.none()
                ),
                many=True,
            ).data,
            # ⑥ PlisTitle ─ 플리 자체 제목 (노트엔 해당 없음)
            "PlisTitle": SearchAllPlisSSPSerializer(
                (
                    plis_qs.filter(title__icontains=keyword)
                    if keyword
                    else plis_qs.none()
                ),
                many=True,
            ).data,
        }

        result = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 통합 조회 성공", "data": result},
            status=status.HTTP_200_OK,
        )


"""
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
class SearchNotesView(BlockFilterMixin, views.APIView):
    block_model = Notes

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

        # --- visibility 필터 추가 ---
        vis_q = Q(visibility="public")
        if request.user.is_authenticated:
            # 내가 팔로우한 사람들의 노트 (friends)
            following_ids = UserFollows.objects.filter(
                follower=request.user
            ).values_list("following_id", flat=True)
            vis_q |= Q(visibility="friends", user__in=following_ids)
            # 내가 쓴 모든 노트 (private 포함)
            vis_q |= Q(user=request.user)
        # vis_q 완성

        # --- 검색 실행 시 visibility도 함께 걸기 ---
        base_q = query & vis_q if has_filter else vis_q
        search_results = Notes.objects.filter(base_q).distinct()

        # 차단된 글·작성자 제외
        search_results = self.filter_blocked(search_results)

        # --- 나머지 결과 그룹핑 & 응답 조립 ---
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
                (
                    search_results.filter(
                        Q(location_name__icontains=keyword)
                        | Q(location_address__icontains=keyword)
                    )
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
        }

        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )
        return Response(
            {"message": "탐색결과 노트 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )


# 통합검색(플리)
class SearchPlisView(BlockFilterMixin, views.APIView):
    block_model = Plis

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

        # --- visibility 필터 추가 ---
        vis_q = Q(visibility="public")
        if request.user.is_authenticated:
            # 친구 공개: 내가 팔로우한 사람들의 플리
            following_ids = UserFollows.objects.filter(
                follower=request.user
            ).values_list("following_id", flat=True)
            vis_q |= Q(visibility="friends", user__in=following_ids)
            # 나의 플리(비공개 포함)
            vis_q |= Q(user=request.user)

        # --- 최종 queryset 생성 ---
        if has_filter:
            base_q = query & vis_q
        else:
            base_q = vis_q

        search_results = Plis.objects.filter(base_q).distinct()

        # 차단된 플리·작성자 제외
        search_results = self.filter_blocked(search_results)

        # --- 결과 그룹핑 & 직렬화 (기존 로직) ---
        data = {
            "Memo": SearchPlisMemoSerializer(
                (
                    search_results.filter(plinotes__note_memo__icontains=keyword)
                    if keyword
                    else search_results
                ),
                many=True,
            ).data,
            "Lyrics": SearchAllPlisSerializer(
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

        filtered_data = (
            data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        )

        return Response(
            {"message": "탐색결과 플리 조회 성공", "data": filtered_data},
            status=status.HTTP_200_OK,
        )

        # # ---------- (6) visibility 필터 ----------
        # me = request.user
        # vis_q = Q(visibility="public")
        # if me.is_authenticated:
        #     following_ids = UserFollows.objects.filter(follower=me).values_list(
        #         "following_id", flat=True
        #     )
        #     vis_q |= Q(visibility="friends", user__in=following_ids)
        #     vis_q |= Q(user=me)  # 내가 쓴 글은 private 도 봄

        # base_q = (query & vis_q) if has_filter else vis_q

        # # ---------- ★ (7) 차단 필터 ----------
        # if me.is_authenticated:
        #     blocked_plis = PliBlock.objects.filter(user=me).values_list(
        #         "pli_id", flat=True
        #     )
        #     blocked_users = UserBlock.objects.filter(user=me).values_list(
        #         "blocked_user_id", flat=True
        #     )

        #     plis_qs = (
        #         Plis.objects.filter(base_q)
        #         .exclude(id__in=blocked_plis)
        #         .exclude(user_id__in=blocked_users)
        #         .distinct()
        #     )
        # else:
        #     plis_qs = Plis.objects.filter(base_q).distinct()

        # # ---------- (8) 결과 직렬화 ----------
        # data = {
        #     "Memo": SearchPlisMemoSerializer(
        #         (
        #             plis_qs.filter(plinotes__note_memo__icontains=keyword)
        #             if keyword
        #             else plis_qs
        #         ),
        #         many=True,
        #     ).data,
        #     "Lyrics": SearchPlisLSSPSerializer(
        #         (
        #             plis_qs.filter(plinotes__notes__lyrics__icontains=keyword)
        #             if keyword
        #             else plis_qs
        #         ),
        #         many=True,
        #     ).data,
        #     "SongTitle": SearchPlisLSSPSerializer(
        #         (
        #             plis_qs.filter(plinotes__notes__song_title__icontains=keyword)
        #             if keyword
        #             else plis_qs
        #         ),
        #         many=True,
        #     ).data,
        #     "Singer": SearchPlisLSSPSerializer(
        #         (
        #             plis_qs.filter(plinotes__notes__artist__icontains=keyword)
        #             if keyword
        #             else plis_qs
        #         ),
        #         many=True,
        #     ).data,
        #     "PlisTitle": SearchPlisLSSPSerializer(
        #         (plis_qs.filter(title__icontains=keyword) if keyword else plis_qs),
        #         many=True,
        #     ).data,
        # }

        # filtered_data = (
        #     data if filter_type == "all" else {filter_type: data.get(filter_type, [])}
        # )
        # return Response(
        #     {"message": "탐색결과 플리 조회 성공", "data": filtered_data},
        #     status=status.HTTP_200_OK,
        # )


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

        # 4) 최종 QuerySet
        qs = User.objects.filter(query).distinct()

        # 5) ★ 차단된 작성자 제외 ─ blocker 필드 사용
        me = request.user
        if me.is_authenticated:
            qs = qs.exclude(id__in=blocked_user_ids(me))  # util 함수 한 줄로 처리

        # 6) 팔로잉·팔로워 annotate
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
            qs = qs.annotate(
                is_following=Value(False, output_field=BooleanField()),
                is_follower=Value(False, output_field=BooleanField()),
            )

        # 7) 직렬화 & 응답
        serializer = SearchWritersSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(
            {"message": "탐색결과 작성자 조회 성공", "data": {"user": serializer.data}},
            status=status.HTTP_200_OK,
        )

        # # 아무 조건도 없으면 빈 결과
        # if query == Q():
        #     return Response(
        #         {"message": "탐색결과 작성자 조회 성공", "data": {"user": []}},
        #         status=status.HTTP_200_OK,
        #     )

        # # (4) 기본 QuerySet
        # qs = User.objects.filter(query).distinct()

        # # ---------- ★ (5) 차단된 작성자 제외 ----------
        # me = request.user
        # if me.is_authenticated:
        #     blocked_user_ids = UserBlock.objects.filter(user=me).values_list(
        #         "blocked_user_id", flat=True
        #     )
        #     if blocked_user_ids:
        #         qs = qs.exclude(id__in=blocked_user_ids)

        # # ---------- (6) 팔로잉 / 팔로워 annotate ----------
        # if me.is_authenticated:
        #     qs = qs.annotate(
        #         is_following=Exists(
        #             UserFollows.objects.filter(follower=me, following=OuterRef("pk"))
        #         ),
        #         is_follower=Exists(
        #             UserFollows.objects.filter(follower=OuterRef("pk"), following=me)
        #         ),
        #     )
        # else:
        #     qs = qs.annotate(
        #         is_following=Value(False, output_field=BooleanField()),
        #         is_follower=Value(False, output_field=BooleanField()),
        #     )

        # # ---------- (7) 직렬화 & 응답 ----------
        # serializer = SearchWritersSerializer(
        #     qs, many=True, context={"request": request}
        # )
        # return Response(
        #     {"message": "탐색결과 작성자 조회 성공", "data": {"user": serializer.data}},
        #     status=status.HTTP_200_OK,
        # )

        """ # 검색 실행
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
 """
