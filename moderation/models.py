# from django.db import models
# from django.conf import settings
# from accounts.models import User
# from notes.models import *

# # Create your models here.


# # 차단 관련 코드(박나담)
# class NoteBlock(models.Model):
#     """사용자가 특정 노트를 차단"""

#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="blocked_notes"
#     )
#     note = models.ForeignKey("Notes", on_delete=models.CASCADE, related_name="blocks")
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "note_blocks"
#         unique_together = ("user", "note")


# class PliBlock(models.Model):
#     """사용자가 특정 플리를 차단"""

#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="blocked_plis"
#     )
#     pli = models.ForeignKey("Plis", on_delete=models.CASCADE, related_name="blocks")
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "pli_blocks"
#         unique_together = ("user", "pli")


# class UserBlock(models.Model):
#     """사용자가 게시글 작성자를 차단"""

#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="blocked_users"
#     )
#     blocked_user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="blocked_by"
#     )
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "user_blocks"
#         unique_together = ("user", "blocked_user")

from django.db import models
from django.conf import settings
from notes.models import Notes, Plis


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_made"
    )
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "blocked_user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ {self.blocked_user}"


class NoteBlock(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.ForeignKey(Notes, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "note")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ note:{self.note_id}"


class PliBlock(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pli = models.ForeignKey(Plis, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "pli")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ pli:{self.pli_id}"
