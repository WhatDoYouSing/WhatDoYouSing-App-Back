from django.utils.crypto import salted_hmac
from django.utils.http import int_to_base36
from django.utils import timezone
from django.conf import settings

class EmailVerificationTokenGenerator:
    key_salt = "accounts.tokens.EmailVerificationTokenGenerator"
    secret = settings.SECRET_KEY

    def make_token(self, email):
        timestamp = int(timezone.now().timestamp())
        value = f"{email}{timestamp}"
        hash = salted_hmac(self.key_salt, value, secret=self.secret).hexdigest()[::2]
        return f"{int_to_base36(timestamp)}-{hash}"

    def check_token(self, email, token):
        try:
            ts_b36, hash = token.split("-")
            timestamp = int(ts_b36, 36)
        except Exception:
            return False

        value = f"{email}{timestamp}"
        expected_hash = salted_hmac(self.key_salt, value, secret=self.secret).hexdigest()[::2]
        return hash == expected_hash