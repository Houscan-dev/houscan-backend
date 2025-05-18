from rest_framework import generics
from .models import Announcement
from .serializers import AnnouncementSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    queryset = Announcement.objects.order_by('-updated_at')
    serializer_class = AnnouncementSerializer

class AnnouncementDetailAPIView(generics.RetrieveAPIView):
    lookup_field = 'file_name'
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
