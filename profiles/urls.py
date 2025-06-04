from django.urls import path
from .views import *

urlpatterns = [
    path('', ProfileView.as_view(), name='profile-detail'),  # patch - 수정, get - 열람
    path('create/', ProfileCreateView.as_view(), name='profile-create'),
]
