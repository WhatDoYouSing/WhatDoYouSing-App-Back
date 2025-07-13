from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError  # 예외 추가

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals
        try:
            from .models import Title
            # 기본 레코드가 없는 경우 생성
            if not Title.objects.exists():
                Title.objects.create(name="blank", condition="왓두유씽 가입", emoji=0)
        except (OperationalError, ProgrammingError):
            # 데이터베이스가 아직 준비되지 않았거나 테이블이 없을 경우 무시
            pass
