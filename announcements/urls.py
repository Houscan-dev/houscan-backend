from django.urls import path
from .views import AnnouncementListAPIView, AnnouncementDetailAPIView
#,AnnouncementDetailAPIView

urlpatterns = [
    path('', AnnouncementListAPIView.as_view(), name='announcement-list'),
    path('<int:id>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
]
