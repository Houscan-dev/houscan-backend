from django.urls import path, include
from rest_framework import urls
from .views import *
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()
router.register('list', UserViewSet) # 유저리스트 (테스트용)

urlpatterns = [
    # 토큰 재발급
    path("signup/",SignupAPIView.as_view()),
    path("auth/", AuthAPIView.as_view()),
    path("password-reset/", PasswordResetRequestAPIView.as_view()),
    path("password-reset/confirm/", PasswordResetConfirmAPIView.as_view()),
    path("delete/", DeleteAPIView.as_view()),
    # 회원 탈퇴
    path('my/', MyAPIView.as_view()),
    path('change-pw/', PwChangeAPIView.as_view()),
    path("", include(router.urls)),
]