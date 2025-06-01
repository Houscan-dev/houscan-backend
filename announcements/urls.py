from django.urls import path
from .views import (
    AnnouncementListAPIView,
    AnnouncementDetailAPIView,
    AnnouncementPDFNameAPIView,
    AnnouncementHouseAPIView,
    HousingEligibilityAnalyzeView
)

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    path('<int:id>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
    path('<int:id>/pdf-name/', AnnouncementPDFNameAPIView.as_view(), name='announcement-pdf-name'),
    path('house/<int:house_id>/', AnnouncementHouseAPIView.as_view(), name='announcement-house'),
    path('<int:announcement_id>/analyze/', HousingEligibilityAnalyzeView.as_view(), name='housing-eligibility-analyze'),
]
