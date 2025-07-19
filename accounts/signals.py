from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import m2m_changed
from django.db import transaction
from django.dispatch import receiver
from django.utils.timezone import now
from .models import *
from notes.models import *
from collects.models import *

@receiver(post_save, sender=User)
def assign_blank_title(sender, instance, created, **kwargs):
    if created:
        try:
            blank_title = Title.objects.get(name="blank")
            UserTitle.objects.get_or_create(user=instance, title=blank_title)
            instance.title_selection = blank_title
            instance.profile = instance.profile or blank_title.emoji
            instance.save()
        except Title.DoesNotExist:
            # logging.warning('Title "blank" does not exist')
            pass

'''
title2 - 왓두유씽뉴비 (노트 최초 등록)
'''

@receiver(post_save, sender=Notes)
def assign_title2(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    title_id = 2 

    already_granted = UserTitle.objects.filter(user=user, title_id=title_id).exists()
    if already_granted:
        return

    note_count = Notes.objects.filter(user=user).count()
    if note_count == 1:
        try:
            with transaction.atomic():
                title = Title.objects.get(id=title_id)
                UserTitle.objects.create(user=user, title=title)
        except Title.DoesNotExist:
            pass  # title이 존재하지 않으면 무시

'''
title3 - 봄마니아 (봄 태그 5회 등록)
title4 - 여름마니아 (여름 태그 5회 등록)
title5 - 가을마니아 (가을 태그 5회 등록)
title6 - 겨울마니아 (겨울 태그 5회 등록)
'''

SEASON_TITLE_MAP = {
    "봄": 3, 
    "여름": 4,
    "가을": 5,
    "겨울": 6,
}

REQUIRED_COUNT = 5

def assign_season_titles(user):
    for season_name, title_id in SEASON_TITLE_MAP.items():
        try:
            season_obj = Seasons.objects.get(name=season_name)
        except Seasons.DoesNotExist:
            continue 

        if UserTitle.objects.filter(user=user, title_id=title_id).exists():
            continue

        note_count = Notes.objects.filter(user=user, tag_season=season_obj).count()
        pli_count = Plis.objects.filter(user=user, tag_season=season_obj).count()
        total = note_count + pli_count

        if total >= REQUIRED_COUNT:
            try:
                with transaction.atomic():
                    title = Title.objects.get(id=title_id)
                    UserTitle.objects.create(user=user, title=title)
            except Title.DoesNotExist:
                continue

@receiver(m2m_changed, sender=Notes.tag_season.through)
def check_season_tag_in_note(sender, instance, action, **kwargs):
    if action == "post_add":
        assign_season_titles(instance.user)

@receiver(m2m_changed, sender=Plis.tag_season.through)
def check_season_tag_in_pli(sender, instance, action, **kwargs):
    if action == "post_add":
        assign_season_titles(instance.user) 

'''
title7 - 행복전도사 (행복 감정 투표 15회)
title8 - 울돌목 (벅참 감정 투표 15회)
'''        

EMOTION_TITLE_MAP = {
    "행복": 7, 
    "벅참": 8, 
}
EMOTION_COUNT = 15

@receiver(post_save, sender=NoteEmotion)
def assign_emotion_titles(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user

    for emotion_name, title_id in EMOTION_TITLE_MAP.items():
        try:
            emotion_obj = Emotions.objects.get(name=emotion_name)
        except Emotions.DoesNotExist:
            continue

        if UserTitle.objects.filter(user=user, title_id=title_id).exists():
            continue

        emotion_count = NoteEmotion.objects.filter(user=user, emotion=emotion_obj).count()

        if emotion_count >= EMOTION_COUNT:
            try:
                with transaction.atomic():
                    title = Title.objects.get(id=title_id)
                    UserTitle.objects.create(user=user, title=title)
            except Title.DoesNotExist:
                continue

'''
title9 - 느좋노래탐험가 (내가 타인의 글을 10회 북마크)
title10 - 뭘좀아는뮤직러버 (타인이 나의 글을 10회 북마크)
'''   
TITLE_BOOKMARK_ID = 9 
TITLE_BOOKMARKED_ID = 10

@receiver(post_save, sender=ScrapNotes)
@receiver(post_save, sender=ScrapPlaylists)
def assign_bookmark_titles(sender, instance, created, **kwargs):
    if not created:
        return

    scrap_user = instance.scrap_list.user 

    # 타이틀 9: 내가 남의 글을 10개 북마크했을 때
    count_others_bookmarked = 0

    scrap_notes = ScrapNotes.objects.filter(scrap_list__user=scrap_user)
    for scrap in scrap_notes:
        try:
            note = Notes.objects.get(id=scrap.content_id)
            if note.user != scrap_user:
                count_others_bookmarked += 1
        except Notes.DoesNotExist:
            continue

    scrap_playlists = ScrapPlaylists.objects.filter(scrap_list__user=scrap_user)
    for scrap in scrap_playlists:
        try:
            pli = Plis.objects.get(id=scrap.content_id)
            if pli.user != scrap_user:
                count_others_bookmarked += 1
        except Plis.DoesNotExist:
            continue

    if count_others_bookmarked >= 10:
        try:
            if not UserTitle.objects.filter(user=scrap_user, title_id=9).exists():
                title = Title.objects.get(id=9)
                UserTitle.objects.create(user=scrap_user, title=title)
        except Title.DoesNotExist:
            pass

    # 타이틀 10: 내 글이 타인에게 10회 이상 북마크되었을 때
    my_user = scrap_user
    count_my_content_bookmarked = 0

    my_note_ids = Notes.objects.filter(user=my_user).values_list("id", flat=True)
    count_my_content_bookmarked += ScrapNotes.objects.filter(
        content_id__in=my_note_ids
    ).exclude(scrap_list__user=my_user).count()

    my_pli_ids = Plis.objects.filter(user=my_user).values_list("id", flat=True)
    count_my_content_bookmarked += ScrapPlaylists.objects.filter(
        content_id__in=my_pli_ids
    ).exclude(scrap_list__user=my_user).count()

    if count_my_content_bookmarked >= 10:
        try:
            if not UserTitle.objects.filter(user=my_user, title_id=10).exists():
                title = Title.objects.get(id=10)
                UserTitle.objects.create(user=my_user, title=title)
        except Title.DoesNotExist:
            pass

'''
title11 - 밴붐온 ("밴드" 단어 15회 등록)
title12 - 밴붐왓 ("밴드" 단어 30회 등록)
title13 - 돌은ROCK ("락" 단어 15회 등록)
title14 - 락스타지망생 ("락" 단어 30회 등록)
title15 - 내전공은KPOP ("케이팝" 단어 15회 등록)
title16 - KPOP박사과정 ("케이팝" 단어 30회 등록)
''' 

KEYWORD_TITLE_MAP = {
    "밴드": (11, 12), 
    "락": (13, 14),
    "케이팝": (15, 16),
}

@receiver(post_save, sender=Notes)
def keyword_title_from_notes(sender, instance, created, **kwargs):
    if not created or not instance.memo:
        return
    user = instance.user
    for keyword in KEYWORD_TITLE_MAP:
        if keyword in instance.memo:
            count = Notes.objects.filter(user=user, memo__contains=keyword).count()
            assign_keyword_title(user, keyword, count)

@receiver(post_save, sender=PliNotes)
def keyword_title_from_plinotes(sender, instance, created, **kwargs):
    if not created or not instance.note_memo:
        return
    user = instance.plis.user
    for keyword in KEYWORD_TITLE_MAP:
        if keyword in instance.note_memo:
            matching_plis_ids = set(
                PliNotes.objects.filter(
                    plis__user=user,
                    note_memo__contains=keyword
                ).values_list("plis_id", flat=True)
            )
            count = len(matching_plis_ids)
            assign_keyword_title(user, keyword, count)

def assign_keyword_title(user, keyword, count):
    title_15, title_30 = KEYWORD_TITLE_MAP[keyword]
    try:
        if count >= 30 and not UserTitle.objects.filter(user=user, title_id=title_30).exists():
            title = Title.objects.get(id=title_30)
            UserTitle.objects.create(user=user, title=title)
        elif count >= 15 and not UserTitle.objects.filter(user=user, title_id=title_15).exists():
            title = Title.objects.get(id=title_15)
            UserTitle.objects.create(user=user, title=title)
    except Title.DoesNotExist:
        pass