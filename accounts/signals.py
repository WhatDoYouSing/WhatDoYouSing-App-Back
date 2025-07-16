from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from .models import *

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
def check_title_conditions(user):
    """
    유저가 특정 행동을 하면 칭호 조건을 만족하는지 검사하고 자동 활성화
    """
    conditions_map = {
        "note_1": ,  # 노트 최초 등록
        "spring_5": ,  # 봄 계절 태그 5회 등록
        "summer_5": ,  # 여름 계절 태그 5회 등록
        "fall_5": ,  # 가을 계절 태그 5회 등록
        "winter_5": ,  # 겨울 계절 태그 5회 등록
        "happy_15": ,  # 커뮤니티(타인의 노트에) 행복 감정 15회 등록
        "overwhelmed_15": ,  # 커뮤니티(타인의 노트에) 벅참 감정 15회 등록
        "mark_10": ,  # 타인의 글을 10회 북마크
        "marked_10": ,  # 내 글이 10회 북마크 됨
        "band_15": ,  # 밴드 단어가 포함된 노트/플리를 15회 등록
        "band_30": ,  # 밴드 단어가 포함된 노트/플리를 30회 등록
        "rock_15": ,  # 락 단어가 포함된 노트/플리를 15회 등록
        "rock_30": ,  # 락 단어가 포함된 노트/플리를 30회 등록
        "kpop_15": ,  # 케이팝 단어가 포함된 노트/플리를 15회 등록
        "kpop_30": ,  # 케이팝 단어가 포함된 노트/플리를 30회 등록
    }

    for title in Title.objects.all():
        condition_key = title.condition  # 예: "login_10"
        check_func = conditions_map.get(condition_key)  

        if check_func and check_func(user):  
            activate_title(user, title)

def activate_title(user, title):
    """칭호 활성화"""
    user_title, created = UserTitle.objects.get_or_create(user=user, title=title)
    if not user_title.is_active:
        user_title.is_active = True
        user_title.acquired_at = now()
        user_title.save()
'''