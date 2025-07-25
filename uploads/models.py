from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# 게시글 작성자 신고
class UserReport(models.Model):
    report_user = models.ForeignKey(
        User,
        verbose_name="신고 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_reports_made",
    )
    issue_user = models.ForeignKey(
        User,
        verbose_name="위험 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_reports_received",
    )
    reason = models.TextField(verbose_name="신고 사유")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_user} → {self.issue_user}"


# 게시글 신고
class PostReport(models.Model):
    REPORT_TYPE_NOTE = "note"
    REPORT_TYPE_PLI = "pli"
    REPORT_NOTE = REPORT_TYPE_NOTE
    REPORT_PLI = REPORT_TYPE_PLI
    REPORT_TYPE_CHOICES = [
        (REPORT_TYPE_NOTE, "Note"),
        (REPORT_TYPE_PLI, "Pli"),
    ]

    report_user = models.ForeignKey(
        User,
        verbose_name="신고 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="post_reports_made",
    )
    issue_user = models.ForeignKey(
        User,
        verbose_name="위험 유저",
        on_delete=models.SET_NULL,
        null=True,
        related_name="post_reports_received",
    )
    report_type = models.CharField(
        max_length=10,
        choices=REPORT_TYPE_CHOICES,
        default=REPORT_TYPE_NOTE,
        verbose_name="신고 대상 타입",
    )
    content_id = models.IntegerField(verbose_name="신고 대상 ID")
    reason = models.TextField(verbose_name="신고 사유")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "post_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_user} reported {self.report_type}#{self.content_id}"
