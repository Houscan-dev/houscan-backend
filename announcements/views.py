from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Announcement
from .serializers import AnnListSerializer #AnnDetailSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]  
    queryset = Announcement.objects.order_by('-updated_at')
    serializer_class = AnnListSerializer

'''class AnnouncementDetailAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    lookup_field = 'file_name'
    queryset = Announcement.objects.all()
    serializer_class = AnnDetailSerializer'''