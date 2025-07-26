from django.apps import AppConfig


class NotifsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifs"

    def ready(self):
        # 앱 로드 시 signals 등록
        from . import signals
