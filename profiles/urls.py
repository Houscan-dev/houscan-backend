from django.urls import path
from .views import *

urlpatterns = [
    # post - 개인정보 입력, patch - 수정, get - 열람
    path('', ProfileView.as_view(), name='profile-detail'),
    path('create/', ProfileCreateView.as_view(), name='profile-create'),
]
