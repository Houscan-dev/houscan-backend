from django.urls import path
from .views import (
    AnnouncementListAPIView,
    AnnouncementDetailAPIView,
    AnnouncementHouseAPIView,
    HousingEligibilityAnalyzeView
)

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    path('<int:id>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
    path('house/<int:house_id>/', AnnouncementHouseAPIView.as_view(), name='announcement-house'),
    path('analyze-all/', HousingEligibilityAnalyzeView.as_view(), name='housing-eligibility-analyze-all'),
]
