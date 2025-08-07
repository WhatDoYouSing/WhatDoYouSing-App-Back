from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(UserBlock)
admin.site.register(NoteBlock)
admin.site.register(PliBlock)
admin.site.register(NoteCommentBlock)
admin.site.register(PliCommentBlock)
admin.site.register(NoteReplyBlock)
admin.site.register(PliReplyBlock)
