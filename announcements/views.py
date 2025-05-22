from rest_framework import generics
from django.shortcuts import get_object_or_404
import json
from rest_framework.response import Response
from django.conf import settings
from pathlib import Path
from rest_framework.permissions import AllowAny
from .models import Announcement
from .serializers import AnnListSerializer
from rest_framework.views import APIView
#AnnDetailSerializer,

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]  
    queryset = Announcement.objects.order_by('-updated_at')
    serializer_class = AnnListSerializer

class JSONFileMixin(APIView):
    permission_classes = [AllowAny]

    def load_for(self, subfolder: str):
        folder = Path(settings.ANNOUNCEMENTS_JSON_ROOT) / subfolder
        if not folder.exists():
            return {"error": f"Folder not found: {folder}"}

        matches = list(folder.glob(f"*_{subfolder}.json"))
        if not matches:
            return {"error": f"No files matching '*_{subfolder}.json' in {folder}"}

        fp = matches[0]
        try:
            return json.loads(fp.read_text(encoding='utf-8'))
        except Exception as e:
            return {"error": f"Failed to parse JSON in {fp.name}: {str(e)}"}

class AnnouncementDetailAPIView(JSONFileMixin):
    permission_classes = [AllowAny]

    def get(self, request, announcement_id):
        ann = get_object_or_404(Announcement, id=announcement_id)
        return Response({
            "id":               announcement_id,
            "file_name":        ann.file_name,
            "schedule":         self.load_for("schedule"),
            "criteria":         self.load_for("criteria"),
            "priority_score":   self.load_for("priority_score"),
            "residence_period": self.load_for("residence_period"),
            "precautions":      self.load_for("precautions"),
            "housing_info":     self.load_for("housing_info"),
        })
