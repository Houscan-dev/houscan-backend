from rest_framework import generics
from django.shortcuts import get_object_or_404
import json, os
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Announcement
from rest_framework.views import APIView
from .models import Announcement, HousingEligibilityAnalysis
from .models import HousingInfo
from .serializers import HousingInfoSerializer, AnnouncementDetailSerializer, OpenAnnouncementSerializer

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes=[AllowAny]

    def get(self, request):
        qs = Announcement.objects.order_by('-announcement_date')
        result = []
        
        for ann in qs:
            posted = ann.announcement_date or ""
            # 현재 로그인한 사용자의 자격 분석 정보 가져오기
            analysis_info = None
            if ann.ai_summary_json:
                # ai_summary_json에 'application_schedule' 키가 있고, 그 안에 
                # 'announcement_date'가 있다면 그것을 사용
                schedule = ann.ai_summary_json.get('application_schedule', {})
                posted_date_raw = schedule.get('announcement_date')
                if posted_date_raw and '미정' not in posted_date_raw:
                     posted = posted_date_raw.replace('-', '.')

                category_user = ann.ai_summary_json.get('category_user', [])
                category_type = ann.ai_summary_json.get('category_type', [])

            # DB에서 직접 가져오기 (디테일과 동일)
            if request.user.is_authenticated:
                try:
                    analysis = HousingEligibilityAnalysis.objects.get(
                        user=request.user,
                        announcement=ann
                    )
                    analysis_info = {
                        'is_eligible': analysis.is_eligible,
                        'priority': analysis.priority
                    }
                except HousingEligibilityAnalysis.DoesNotExist:
                    pass

            result.append({
                "id": ann.id,
                "title": ann.title,
                "announcement_date": posted,
                "status": ann.status,
                "category_user": category_user,
                "category_type": category_type,
                "analysis": analysis_info # 자격 O/X 여부
            })
        return Response(result)
    
class AnnouncementDetailAPIView(APIView):
    permission_classes=[AllowAny]
    
    def get(self, request, id):
        ann = get_object_or_404(Announcement, id=id)
        serializer = AnnouncementDetailSerializer(ann)
        data = serializer.data
        ai_summary = data.get("ai_summary_json", {})
        posted = ann.announcement_date or ""
        schedule_data = ai_summary.get("application_schedule", {})
        if schedule_data:
            posted_date_raw = schedule_data.get("announcement_date")
            if posted_date_raw and '미정' not in posted_date_raw:
                posted = posted_date_raw.replace('-', '.')
        data["announcement_date"] = posted

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
        data["analysis"] = analysis_info
        data["ai_precaution"] = (
            "본 정보는 AI를 활용하여 요약되었으며, 정확성이 보장되지 않을 수 있으므로 "
            "참고용으로만 사용하시기 바랍니다. 더 자세한 정보는 아래의 첨부파일을 참고하세요."
        )
        return Response(data)
    
class AnnouncementHouseAPIView(APIView):
    permission_classes=[AllowAny]
    def get(self, request, house_id):
        try:
            house = get_object_or_404(HousingInfo, id=house_id)
            serializer = HousingInfoSerializer(house)
            
            return Response({
                    "success": True,
                    "housing_info": serializer.data,
                }, status=status.HTTP_200_OK)
                
        except HousingInfo.DoesNotExist:
            return Response({
                "success": False,
                "error": f"ID {house_id}에 해당하는 주택 정보가 없습니다.",
                "available_ids": list(HousingInfo.objects.values_list('id', flat=True)[:10])
            }, status=status.HTTP_404_NOT_FOUND)
 
class OpenAnnouncementAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            Announcement.objects
            .filter(status__in=['open','upcoming'])
            .order_by('-announcement_date')
            .prefetch_related('housing_info_list')
        )

        serializer = OpenAnnouncementSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
