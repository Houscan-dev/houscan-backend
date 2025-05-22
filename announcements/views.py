from rest_framework import generics
from django.shortcuts import get_object_or_404
import json, os
from rest_framework.response import Response
from django.conf import settings
from pathlib import Path
from rest_framework.permissions import AllowAny
from .models import Announcement
from rest_framework.views import APIView
from .models import Announcement, AnnouncementDocument

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes=[AllowAny]
    def get(self, request):
        qs = Announcement.objects.order_by('-posted_date')
        data = [
            {
                "id": ann.id,
                "title": ann.title,
                "posted_date": ann.posted_date,
                "status": ann.status,
            }
            for ann in qs
        ]
        return Response(data)
    
class AnnouncementDetailAPIView(APIView):
    permission_classes=[AllowAny]
    def load_for(self, announcement, doc_type):
        try:
            doc = announcement.documents.get(doc_type=doc_type)
        except AnnouncementDocument.DoesNotExist:
            return None
        with open(doc.data_file.path, encoding='utf-8') as fp:
            return json.load(fp)
        data.pop('announcement_id', None)

        if (isinstance(data, dict)and len(data) == 1 and doc_type in data):
            return data[doc_type]

        return data

    
    def get(self, request, id):
        ann = get_object_or_404(Announcement, id=id)
        return Response({
            "id":               ann.id,
            "title":            ann.title,
            "posted_date":      ann.posted_date,
            "status":           ann.status,
            "schedule":         self.load_for(ann, "schedule"),
            "criteria":         self.load_for(ann, "criteria"),
            "housing_info":     self.load_for(ann, "housing_info"),
            "precautions":      self.load_for(ann, "precautions"),
            "priority_score":   self.load_for(ann, "priority_score"),
            "residence_period": self.load_for(ann, "residence_period"),
            "ai_precaution": (
                "본 정보는 AI를 활용하여 요약되었으며, 정확성이 보장되지 않을 수 있으므로 "
                "참고용으로만 사용하시기 바랍니다. 더 자세한 정보는 아래의 첨부파일을 참고하세요."
            ),
        })