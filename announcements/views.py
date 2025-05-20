from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Ann_List
from .serializers import AnnListSerializer, AnnDetailSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]   
    queryset = Ann_List.objects.order_by('-updated_at')
    serializer_class = AnnListSerializer
'''
class AnnouncementDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny] 
    queryset = Ann_Detail.objects.all()
    serializer_class = AnnDetailSerializer
'''