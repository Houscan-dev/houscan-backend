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
from .serializers import HousingInfoSerializer
from profiles.tasks import analyze_user_eligibility_task
from profiles.models import Profile
from .services.eligibility_service import analyze_user_eligibility
from django.db import transaction

class AnnouncementListAPIView(generics.ListAPIView):
    permission_classes=[AllowAny]

    def get(self, request):
        qs = Announcement.objects.order_by('-announcement_date')
        result = []
        # 로그인한 경우, 분석 결과를 미리 한 번에 가져옴
        analysis_map = {}
        if request.user.is_authenticated:
            analyses = HousingEligibilityAnalysis.objects.filter(user=request.user)
            analysis_map = {analysis.announcement_id: analysis for analysis in analyses}

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

            analysis = analysis_map.get(ann.id)
            analysis_info = {
                'is_eligible': analysis.is_eligible
            } if analysis else None

            result.append({
                "id": ann.id,
                "title": ann.title,
                "announcement_date": posted,
                "status": ann.status,
                "analysis": analysis_info # 자격 O/X 여부 
            })
        return Response(result)
    
class AnnouncementDetailAPIView(APIView):
    permission_classes=[AllowAny]
    
    def get(self, request, id):
        ann = get_object_or_404(Announcement, id=id)
        ai_summary = ann.ai_summary_json or {}
        posted = ann.announcement_date or ""
        schedule_data = ai_summary.get("application_schedule", {})
        if schedule_data:
            posted_date_raw = schedule_data.get("announcement_date")
            if posted_date_raw and '미정' not in posted_date_raw:
                posted = posted_date_raw.replace('-', '.')
        
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
            "announcement_date":      posted,
            "status":           ann.status,
            "pdf_name":         ann.pdf_name,
            "ai_summary_json":  ai_summary,
            "housing_info": HousingInfoSerializer(
                HousingInfo.objects.filter(announcement=ann),
                many=True
            ).data,
            "analysis":         analysis_info,  # 자격 분석 결과
            "ai_precaution": (
                "본 정보는 AI를 활용하여 요약되었으며, 정확성이 보장되지 않을 수 있으므로 "
                "참고용으로만 사용하시기 바랍니다. 더 자세한 정보는 아래의 첨부파일을 참고하세요."
            ),
        })
    
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
    
    # ⬇️ [수정] GET -> POST 
    # (GET은 서버 데이터를 변경하지 않아야 하며, 
    #  이렇게 무거운 작업은 POST로 처리하는 것이 표준입니다.)
    @transaction.atomic # ⬅️ 모든 DB 저장을 하나의 작업으로 묶음
    def post(self, request):
        user = request.user
        
        # --- 1. profiles/tasks.py의 로직을 여기로 가져옵니다 ---
        try:
            # 1.1. 사용자 프로필(O/X 판단 재료)을 가져옵니다.
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found. 먼저 프로필을 입력해주세요."}, status=status.HTTP_404_NOT_FOUND)

        # 1.2. 프로필 객체 -> LLM이 이해하는 user_data (dict)로 변환
        # (!!중요!!: profile.is_university_student 같은 필드명은
        #  실제 님의 profiles/models.py 필드명과 일치해야 합니다)
        user_data = {
            "id": user.id,
            "age": profile.age, 
            "birth_date": profile.birth_date.strftime("19%s.%m.%d") if int(profile.birth_date[:2]) > 25 else profile.birth_date.strftime("20%s.%m.%d"), # (날짜 변환 예시)
            "is_married": profile.is_married,
            "residence": profile.residence,
            "university": profile.is_university_student, # (필드명 예시)
            "graduate": profile.is_graduate, # (필드명 예시)
            "employed": profile.is_employed, # (필드명 예시)
            "job_seeker": profile.is_job_seeker, # (필드명 예시)
            "welfare_receipient": profile.is_welfare_receipient, # (필드명 예시)
            "parents_own_house": profile.parents_own_house, # (필드명 예시)
            "disability_in_family": profile.disability_in_family, # (필드명 예시)
            "subscription_account": profile.subscription_account, # (필드명 예시)
            "total_assets": profile.total_assets, # (필드명 예시)
            "car_value": profile.car_value, # (필드명 예시)
            "income_range": profile.income_range, # (필드명 예시)
        }

        # 1.3. O/X 판단 엔진(모델)이 로드되었는지 확인
        if analysis_service.pipe is None:
            return Response({"error": "Qwen 판단 모델이 로드되지 않았습니다. (서버 로그 확인 필요)"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 1.4. [테스트용] 이 사용자의 '이전' 분석 결과를 모두 삭제
        HousingEligibilityAnalysis.objects.filter(user=user).delete()

        # --- 2. 모든 공고를 순회하며 *동기식*으로 분석 (느린 부분) ---
        all_announcements = Announcement.objects.filter(status__in=['open', 'upcoming'])
        
        results_for_response = {} # API 응답으로 돌려줄 딕셔너리
        
        for ann in all_announcements:
            ai_summary = ann.ai_summary_json
            if not ai_summary:
                continue

            try:
                criteria_str = ai_summary.get("application_eligibility", "정보 없음")
                priority_data = ai_summary.get("priority_and_bonus", {})

                # LLM 호출 1: 자격 판단
                eligibility_result = analysis_service.check_eligibility_with_llm(
                    user_data, criteria_str, {}
                )
                
                is_eligible = eligibility_result.get("is_eligible", False)
                reasons = eligibility_result.get("reasons", [])
                priority_str = None

                # LLM 호출 2: 우선순위 판단 (자격이 될 경우)
                if is_eligible:
                    priority_result = analysis_service.check_priority_with_llm(
                        user_data, priority_data
                    )
                    priority_str = priority_result.get("priority", "판단 불가")
                
                # 3. 결과를 DB에 저장 (List/Detail 뷰가 읽을 수 있도록)
                HousingEligibilityAnalysis.objects.create(
                    user=user,
                    announcement=ann,
                    is_eligible=is_eligible,
                    priority=priority_str or "해당없음",
                    reasons=reasons
                )
                
                # 4. API로 즉시 반환할 결과에도 추가
                results_for_response[ann.id] = {
                    'title': ann.title,
                    'is_eligible': is_eligible,
                    'priority': priority_str or "해당없음",
                    'reasons': reasons
                }

            except Exception as e:
                # LLM 호출 중 오류가 나도 멈추지 않고, 오류로 기록
                results_for_response[ann.id] = {
                    'title': ann.title,
                    'is_eligible': False,
                    'priority': "분석 오류",
                    'reasons': [str(e)]
                }
        
        # 5. 모든 분석이 끝난 후, 전체 결과를 API 응답으로 반환
        return Response({
            'success': True,
            'message': f"동기식 분석 완료. {len(results_for_response)}개 공고 처리.",
            'analysis_results': results_for_response
        }, status=status.HTTP_200_OK)
    
    '''
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = str(request.user.id)
        # 비동기 분석 트리거
        analyze_user_eligibility_task.delay(user_id)
        return Response({
            'success': True,
            'message': '분석 요청이 접수되었습니다. 잠시 후 결과를 확인하세요.'
        }, status=status.HTTP_202_ACCEPTED)'''
        