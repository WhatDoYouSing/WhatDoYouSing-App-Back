from django.urls import path
from .views import *

urlpatterns = [
    path('terms/', TermView.as_view()),
    path('signup/', SignUpView.as_view()),
    path('login/', LogInView.as_view()),
    path('duplicate/', DuplicateIDView.as_view()),
    path('update/id/', ChangeUsernameView.as_view()),
    path('update/pw/', ChangePasswordView.as_view()),
    path('delete/', UserDeleteView.as_view()),
    path('random/id/', RandomUsernameView.as_view()),
    path('random/nickname/', RandomNicknameView.as_view()),

    path('kakao/', KakaoLoginView.as_view()),
    path('kakao/callback/',KakaoCallbackView.as_view()),
    path('kakao/delete/', KUserDeleteView.as_view()),
]