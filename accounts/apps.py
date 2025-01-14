from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from .models import Title
        # 기본 레코드가 없는 경우 생성
        if not Title.objects.exists():
            Title.objects.create(name="blank", condition="왓두유씽 가입", emoji=0)
