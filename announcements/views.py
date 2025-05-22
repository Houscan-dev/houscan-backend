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
            return None

        # "*_{subfolder}.json" 패턴 파일 중 첫 번째를 찾는다
        matches = list(folder.glob(f"*_{subfolder}.json"))
        if not matches:
            return None

        fp = matches[0]
        try:
            raw = json.loads(fp.read_text(encoding='utf-8'))
        except Exception:
            return None

        # 만약 raw가 {"residence_period": "..."} 처럼
        # subfolder 키 하나만 가지고 있으면, 그 값을 바로 리턴
        if isinstance(raw, dict) and len(raw) == 1 and subfolder in raw:
            return raw[subfolder]
        
        return raw

    
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
            "ai_precaution": (
                "본 정보는 AI를 활용하여 요약되었으며, 정확성이 보장되지 않을 수 있으므로 "
                "참고용으로만 사용하시기 바랍니다. 더 자세한 정보는 아래의 첨부파일을 참고하세요."
            ),
        })
