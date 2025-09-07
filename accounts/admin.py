from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(UserDeletion)
admin.site.register(Title)
admin.site.register(UserTitle)
admin.site.register(VerifyEmail)
admin.site.register(WithdrawalReason)