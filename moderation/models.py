from django.db import models
from django.conf import settings
from notes.models import Notes, Plis, NoteComment, PliComment, NoteReply, PliReply


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


class NoteCommentBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_note_comments",
    )
    comment = models.ForeignKey(
        NoteComment, on_delete=models.CASCADE, related_name="blocks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "note_comment_blocks"
        unique_together = ("blocker", "comment")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ NoteComment:{self.comment_id}"


class PliCommentBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_pli_comments",
    )
    comment = models.ForeignKey(
        PliComment, on_delete=models.CASCADE, related_name="blocks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pli_comment_blocks"
        unique_together = ("blocker", "comment")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ PliComment:{self.comment_id}"


class NoteReplyBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_note_replies",
    )
    reply = models.ForeignKey(
        NoteReply, on_delete=models.CASCADE, related_name="blocks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "note_reply_blocks"
        unique_together = ("blocker", "reply")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ NoteReply:{self.reply_id}"


class PliReplyBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_pli_replies",
    )
    reply = models.ForeignKey(PliReply, on_delete=models.CASCADE, related_name="blocks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pli_reply_blocks"
        unique_together = ("blocker", "reply")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} ⟶ PliReply:{self.reply_id}"
