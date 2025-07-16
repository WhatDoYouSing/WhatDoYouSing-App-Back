from django.db import models

class WordStat(models.Model):
    user  = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    year  = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    noun  = models.CharField(max_length=100)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year", "month", "noun"],
                name="uniq_user_ym_noun",        
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "year", "month"],
                name="idx_user_ym",
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.year}-{self.month:02d} {self.noun}({self.count})"


class NoteWord(models.Model):
    note = models.ForeignKey("notes.Notes", on_delete=models.CASCADE)
    noun = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["note", "noun"],
                name="uniq_note_noun",
            )
        ]

    def __str__(self):
        return f"{self.note_id} ▸ {self.noun}"