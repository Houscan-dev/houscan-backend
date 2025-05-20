from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Announcement
from .serializers import AnnListSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]   
    queryset = Announcement.objects.order_by('-updated_at')
    serializer_class = AnnListSerializer
'''
class AnnouncementDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny] 
    queryset = Ann_Detail.objects.all()
    serializer_class = AnnDetailSerializer
'''