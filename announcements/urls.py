from django.urls import path
from .views import (
    AnnouncementListAPIView,
    AnnouncementDetailAPIView,
    AnnouncementHouseAPIView,
    OpenAnnouncementAPIView
)

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    path('open/', OpenAnnouncementAPIView.as_view(), name='announcement-open'),
    path('house/<int:house_id>/', AnnouncementHouseAPIView.as_view(), name='announcement-house'),
    path('<int:id>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
]

