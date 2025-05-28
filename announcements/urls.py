from django.urls import path
from .views import AnnouncementListAPIView, AnnouncementDetailAPIView, AnnouncementPDFNameAPIView,AnnouncementHouseAPIView

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    path('<int:id>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
    path('<int:id>/pdf-name/', AnnouncementPDFNameAPIView.as_view(), name='announcement-pdf-name'),  # 추가된 경로
    path('house/<int:house_id>/', AnnouncementHouseAPIView.as_view(), name='announcement-housing_info'),
]
