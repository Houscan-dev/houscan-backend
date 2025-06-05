from rest_framework import generics
from django.shortcuts import get_object_or_404
import json, os
from rest_framework.response import Response
from rest_framework import status
from pathlib import Path
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Announcement
from rest_framework.views import APIView
from .models import Announcement, AnnouncementDocument, HousingEligibilityAnalysis
from .models import HousingInfo
from .serializers import HousingInfoSerializer
from .housing_eligibility_analyzer import analyze_user_eligibility
from django.utils import timezone
from profiles.tasks import analyze_user_eligibility_task
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
            posted = schedule_json.get("announcement_date") or ann.posted_date.isoformat()
            
            # 현재 로그인한 사용자의 자격 분석 정보 가져오기
            analysis_info = None
            if request.user.is_authenticated:
                try:
                    analysis = HousingEligibilityAnalysis.objects.get(
                        user=request.user,
                        announcement=ann
                    )
                    analysis_info = {
                        'priority': analysis.priority
                    }
                except HousingEligibilityAnalysis.DoesNotExist:
                    pass

            result.append({
                "id": ann.id,
                "title": ann.title,
                "posted_date": posted,
                "status": ann.status,
                "analysis": analysis_info
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

        # 현재 로그인한 사용자의 자격 분석 정보 가져오기
        analysis_info = None
        if request.user.is_authenticated:
            try:
                analysis = HousingEligibilityAnalysis.objects.get(
                    user=request.user,
                    announcement=ann
                )
                analysis_info = {
                    'is_eligible': analysis.is_eligible,
                    'priority': analysis.priority,
                    'reasons': analysis.reasons if hasattr(analysis, 'reasons') else [],
                    'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None
                }
            except HousingEligibilityAnalysis.DoesNotExist:
                pass

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
            "analysis":         analysis_info,  # 자격 분석 정보 추가
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
 
class HousingEligibilityAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, announcement_id):
        user_id = str(request.user.id)
        # 비동기 분석 트리거
        analyze_user_eligibility_task.delay(user_id)
        return Response({
            'success': True,
            'message': '분석 요청이 접수되었습니다. 잠시 후 결과를 확인하세요.'
        }, status=status.HTTP_202_ACCEPTED)
        