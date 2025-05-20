from django.urls import path
from .views import AnnouncementListAPIView

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    #path('<int:pk>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
]
