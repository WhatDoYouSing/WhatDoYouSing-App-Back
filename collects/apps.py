from django.apps import AppConfig


class CollectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "collects"

    def ready(self):
        # signal 핸들러 등록
        import collects.signals
