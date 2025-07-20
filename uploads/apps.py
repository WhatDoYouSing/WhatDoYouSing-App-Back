from django.apps import AppConfig


class UploadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "uploads"

    # collects/models.py를 바꿀 수 없어 변경
    def ready(self):
        # 모델 import
        from collects.models import ScrapNotes
        from notes.models import Notes

        # content_object 프로퍼티를 동적으로 추가
        def _get_content_object(self):
            try:
                return Notes.objects.get(pk=self.content_id)
            except Notes.DoesNotExist:
                return None

        ScrapNotes.content_object = property(_get_content_object)
