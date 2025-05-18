from django.urls import path
from .views import AnnouncementListAPIView, AnnouncementDetailAPIView

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='ann-list'),
    path('<path:file_name>/', AnnouncementDetailAPIView.as_view(), name='ann-detail'),
]
