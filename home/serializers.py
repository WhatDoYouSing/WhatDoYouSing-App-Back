from rest_framework import serializers
from notes.models import *
from accounts.models import User
from playlists.models import *


# 유저 정보 직렬화
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'profile']


# 노트 직렬화
class NoteSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    user = UserSerializer()
    title = serializers.SerializerMethodField()
    lyric = serializers.SerializerMethodField()
    emotion = serializers.SerializerMethodField()
    class Meta:
        model = Notes
        fields = [
            'type', 'id', 'user', 'created_at', 'is_updated', 'visibility', 
            'emotion', 'title', 'lyric', 'album_art', 'memo', 'link'
        ]
    def get_type(self,obj):
        return "note"
    def get_title(self,obj):
        return obj.song_title+" - "+obj.artist
    def get_lyric(self,obj):
        return obj.lyrics
    def get_emotion(self,obj):
        return obj.emotion.name

# 플리 직렬화
class PliSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    user = UserSerializer()
    title = serializers.SerializerMethodField()
    lyric = serializers.SerializerMethodField()
    emotion = serializers.SerializerMethodField()
    album_art = serializers.SerializerMethodField()
    memo = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    class Meta:
        model = Plis
        fields = [
            'type', 'id', 'user', 'created_at', 'is_updated', 'visibility', 
            'emotion', 'title', 'lyric', 'album_art', 'memo', 'link'
        ]
    def get_type(self,obj):
        return "pli"
    def get_title(self,obj):
        return "노트 "+str(PliNotes.objects.filter(plis=obj).count())
    def get_lyric(self,obj):
        return obj.title
    def get_emotion(self,obj):
        return None
    def get_memo(self,obj):
        first_note = PliNotes.objects.filter(plis=obj).first()
        if first_note:
            return first_note.note_memo  
        return None 
    def get_link(self,obj):
        first_note = PliNotes.objects.filter(plis=obj).first()
        if first_note:
            return first_note.notes.link  
        return None 
    def get_album_art(self,obj):
        first_four_album_arts = PliNotes.objects.filter(plis=obj).values_list('notes__album_art', flat=True)[:4]
    
        # 앨범 아트 리스트가 비어 있지 않으면 반환, 없으면 None
        if first_four_album_arts:
            return list(first_four_album_arts)
        
        return None

        

# 홈 통합 직렬화
# class HomeContentSerializer(serializers.Serializer):
#     content = serializers.SerializerMethodField()

#     def get_content(self, obj):
#         if obj['type'] == 'note':
#             return NoteSerializer(obj['content']).data
#         elif obj['type'] == 'pli':
#             return PliSerializer(obj['content']).data
#         return {}
    


class HomeContentSerializer(serializers.Serializer):
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        if obj.type == 'note':
            return NoteSerializer(obj.content).data  # obj.content는 Note 객체여야 함
        elif obj.type == 'pli':
            return PliSerializer(obj.content).data  # obj.content는 Pli 객체여야 함
        return {}
