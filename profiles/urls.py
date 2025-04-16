from django.urls import path
from .views import *

urlpatterns = [
    # put - 개인정보 입력, patch - 수정, get - 열람
    path('', ProfileView.as_view(), name='profile'),
]
