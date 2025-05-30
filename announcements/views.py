from rest_framework import generics
from django.shortcuts import get_object_or_404
import json, os
from rest_framework.response import Response
from rest_framework import status
from pathlib import Path
from rest_framework.permissions import AllowAny
from .models import Announcement
from rest_framework.views import APIView
from .models import Announcement, AnnouncementDocument
from .models import HousingInfo
from .serializers import HousingInfoSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes=[AllowAny]
    def load_schedule(self, announcement):
        try:
            doc = announcement.documents.get(doc_type="schedule")
            with open(doc.data_file.path, encoding='utf-8') as fp:
                return json.load(fp)
        except (AnnouncementDocument.DoesNotExist, json.JSONDecodeError, OSError):
            return {}
    
    def get(self, request):
        qs = Announcement.objects.order_by('-posted_date')
        result = []
        for ann in qs:
            schedule_json = self.load_schedule(ann)
            # JSON에서 announcement_date를 꺼내되, 없으면 모델의 posted_date로 대체
            posted = schedule_json.get("announcement_date")
            if not posted:
                # DateField를 문자열로 바꿔 줄 때는 isoformat() 권장
                posted = ann.posted_date.isoformat()
            result.append({
                "id":          ann.id,
                "title":       ann.title,
                "posted_date": posted,
                "status":      ann.status,
            })

        return Response(result)
    
class AnnouncementDetailAPIView(APIView):
    permission_classes=[AllowAny]
    def load_for(self, announcement, doc_type):
        try:
            doc = announcement.documents.get(doc_type=doc_type)
            with open(doc.data_file.path, encoding='utf-8') as fp:
                data = json.load(fp)
        except (AnnouncementDocument.DoesNotExist, OSError, json.JSONDecodeError):
            return None
        
        data.pop('announcement_id', None)

        if isinstance(data, dict) and doc_type in data:
            return data[doc_type]

        return data
    
    def get(self, request, id):
        ann = get_object_or_404(Announcement, id=id)
        schedule_json = self.load_for(ann, "schedule") or {}
        posted = schedule_json.get("announcement_date")
        if not posted:
            posted = ann.posted_date.isoformat()
        return Response({
            "id":               ann.id,
            "title":            ann.title,
            "posted_date":      posted,
            "status":           ann.status,
            "pdf_name":         ann.pdf_name,
            "schedule":         self.load_for(ann, "schedule"),
            "criteria":         self.load_for(ann, "criteria"),
            "housing_info": HousingInfoSerializer(
            HousingInfo.objects.filter(announcement=ann),
            many=True
            ).data,
            "precautions":      self.load_for(ann, "precautions"),
            "priority_score":   self.load_for(ann, "priority_score"),
            "residence_period": self.load_for(ann, "residence_period"),
            "ai_precaution": (
                "본 정보는 AI를 활용하여 요약되었으며, 정확성이 보장되지 않을 수 있으므로 "
                "참고용으로만 사용하시기 바랍니다. 더 자세한 정보는 아래의 첨부파일을 참고하세요."
            ),
        })
    
class AnnouncementPDFNameAPIView(APIView):
    permission_classes=[AllowAny]
    def get(self, request, id):
        announcement = get_object_or_404(Announcement, id=id)
        pdf_name = announcement.pdf_name
        title = announcement.title
        return Response({"pdf_name": pdf_name,
                        "title":title}, 
                        status=status.HTTP_200_OK)
    
class AnnouncementHouseAPIView(APIView):
    permission_classes=[AllowAny]
    def get(self, request, house_id):
        house = get_object_or_404(HousingInfo, id=house_id)
        serializer = HousingInfoSerializer(house)
        
        return Response({
            "housing_info": serializer.data,
        }, status=status.HTTP_200_OK)