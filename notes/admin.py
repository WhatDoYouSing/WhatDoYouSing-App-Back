from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Emotions)
admin.site.register(Times)
admin.site.register(Seasons)
admin.site.register(Contexts)
admin.site.register(Notes)
admin.site.register(Plis)
admin.site.register(PliNotes)
admin.site.register(NoteEmotion)
admin.site.register(NoteComment)
admin.site.register(NoteReply)
admin.site.register(PliComment)
admin.site.register(PliReply)
admin.site.register(CommentReport)
admin.site.register(UserBlock)
admin.site.register(NoteBlock)
admin.site.register(PliBlock)
