from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from accounts.models import *
from notes.models import Notes, Plis, PliNotes
import random
from social.models import *

User = get_user_model()

# 📌 마이페이지 기본
class MyPageSerializer(serializers.ModelSerializer):
    follower = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()

    class Meta:
        model = User
        #팔로워 팔로우 목록 api 추가되면 카운트 가져오기
        fields = ['id','profile','title_selection','serviceID', 'nickname','follower','following','auth_provider', 'email']

    def get_follower(self, obj):
        # 팔로우 당한 사람 = 나를 팔로우한 유저 수
        return UserFollows.objects.filter(following=obj).count()

    def get_following(self, obj):
        # 내가 팔로우한 유저 수
        return UserFollows.objects.filter(follower=obj).count()

# 📌 내 노트 Serializer 
class MyNoteSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    serviceID = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Notes
        fields = [
            'type', 'id', 'user', 'serviceID', 'nickname', 'profile', 'created_at', 'is_updated', 'visibility', 
            'emotion', 'song_title', 'artist', 'lyrics', 'album_art', 'memo'
        ]
    def get_type(self,obj):
        return "note"
    
    def get_serviceID(self, obj):
        return obj.user.serviceID if isinstance(obj.user, User) else None

    def get_nickname(self, obj):
        return obj.user.nickname if isinstance(obj.user, User) else None

    def get_profile(self, obj):
        return obj.user.profile if isinstance(obj.user, User) else None

# 📌 내 플리 Serializer 
class MyPliSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    serviceID = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()
    pli_memo = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()

    # 플리 안에 노트 몇개인지
    # 플리 내용

    class Meta:
        model = Plis
        fields = [
            'type', 'id', 'title', 'album_art', 'note_count', 'pli_memo', 'user', 'serviceID', 'nickname', 'profile', 'created_at', 'is_updated', 'visibility', 
        ]

    def get_type(self,obj):
        return "pli"
    
    def get_serviceID(self, obj):
        return obj.user.serviceID if isinstance(obj.user, User) else None

    def get_nickname(self, obj):
        return obj.user.nickname if isinstance(obj.user, User) else None

    def get_profile(self, obj):
        return obj.user.profile if isinstance(obj.user, User) else None
    
    def get_note_count(self, obj):
        return PliNotes.objects.filter(plis=obj).count()
    
    def get_pli_memo(self, obj):
        memo = (
            PliNotes.objects.filter(plis=obj)
            .order_by('created_at', 'id')
            .values_list('note_memo', flat=True)
            .first()
        )
        return memo
    
    def get_album_art(self, obj):
        first_four_album_arts = PliNotes.objects.filter(plis=obj).values_list(
            "notes__album_art", flat=True
        )[:4]

        # 앨범 아트 리스트가 비어 있지 않으면 반환, 없으면 None
        if first_four_album_arts:
            return list(first_four_album_arts)

        return None

# 📌 내 보관함 Serializer 
#class MyCollectionSerializer(serializers.ModelSerializer):

# ✅ 닉네임 편집 Serializer
class NicknameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','nickname']

# ✅ 전체 칭호 Serializer
class TitleListSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ['id', 'name', 'emoji', 'is_active']

    def get_is_active(self, obj):
        user = self.context.get('user')
        return UserTitle.objects.filter(user=user, title=obj).exists()

# ✅ 유저 획득 칭호 Serializer
class ActiveUserTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    class Meta:
        model = UserTitle
        fields = ['title']
    
    def get_title(self, obj):
        return obj.title.name

# ✅ 유저 칭호 변경 Serializer
class UserTitleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['title_selection']

# ✅ 유저 획득 이모지(프로필) Serializer
class ActiveUserProfileSerializer(serializers.ModelSerializer):
    profile = serializers.IntegerField()

# ✅ 닉네임 변경 Serializer
class NicknameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname']
'''
# 📌 달력 뷰 노트 썸네일
class NoteThumbnailSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Notes
        fields = ['type', 'id','song_title','album_art']

    def get_type(self,obj):
        return "note"

# 📌 달력 뷰 플리 썸네일
class PliThumbnailSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    album_arts = serializers.SerializerMethodField() 

    class Meta:
        model = Plis
        fields = ['type', 'id', 'title', 'album_arts'] 

    def get_album_arts(self, obj):
        note_thumbnails = obj.plinotes.order_by('created_at').values_list('notes__album_art', flat=True)[:4]

        return [art for art in note_thumbnails if art]
    
    def get_type(self,obj):
        return "pli"

        #불러온 플리의 아이디를 가진 PliNotes 객체에 접근, 오래된 순으로 노트 id에 최대 4개 접근해 그 앨범아트를 가져와야 함
'''