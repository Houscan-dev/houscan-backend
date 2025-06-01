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
        """현재 로그인된 사용자의 자격을 분석"""
        try:
            # 공고 정보 가져오기
            announcement = get_object_or_404(Announcement, id=announcement_id)
            
            # 현재 로그인된 사용자의 자격만 분석
            user_id = str(request.user.id)
            print(f"분석할 사용자 ID: {user_id}")  # 디버깅 로그
            
            try:
                # 자격 분석 실행
                results = analyze_user_eligibility(user_id)
                print(f"분석 결과: {results}")  # 디버깅 로그
                
                # 해당 공고의 결과만 추출
                announcement_result = results.get(announcement_id)
                if not announcement_result:
                    return Response({
                        'success': False,
                        'error': f'공고 ID {announcement_id}에 대한 분석 결과가 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # 분석 결과를 데이터베이스에 저장
                HousingEligibilityAnalysis.objects.update_or_create(
                    user=request.user,
                    announcement=announcement,
                    defaults={
                        'is_eligible': announcement_result['is_eligible'],
                        'priority': announcement_result['priority'],
                        'reasons': announcement_result.get('reasons', []),
                        'analyzed_at': timezone.now()
                    }
                )
                
                return Response({
                    'success': True,
                    'data': {
                        'is_eligible': announcement_result['is_eligible'],
                        'priority': announcement_result['priority'],
                        'reasons': announcement_result.get('reasons', []),
                        'user_id': user_id,
                        'announcement_id': announcement_id
                    },
                    'message': '자격 분석이 완료되었습니다.'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'자격 분석 중 오류가 발생했습니다: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'처리 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)