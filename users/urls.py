from django.urls import path, include
from rest_framework import urls
from .views import *
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()
router.register('list', UserViewSet) # 유저리스트 (테스트용)

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    # 토큰 재발급
    path("signup/",SignupAPIView.as_view()),
    path("auth/", AuthAPIView.as_view()),
    # post - 로그인, get - 유저정보, delete - 로그아웃
    path("delete/", DeleteAPIView.as_view()),
    # 회원 탈퇴
    path('my/', MyAPIView.as_view()),
    path('change-pw/', PwChangeAPIView.as_view()),
    path("", include(router.urls)),
]
