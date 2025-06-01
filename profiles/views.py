from rest_framework import generics, permissions
from .models import Profile
from .serializers import ProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
import threading
from announcements.housing_eligibility_analyzer import process_multiple_announcements
from announcements.models import Announcement, HousingEligibilityAnalysis

def analyze_eligibility_async(user_id: str):
    """
    백그라운드에서 자격 분석을 수행하는 함수
    """
    try:
        # 모든 공고에 대해 분석
        announcements = Announcement.objects.all()
        results = process_multiple_announcements(announcements, str(user_id))
        
        # 결과 저장
        for announcement_id, result in results.items():
            try:
                announcement = Announcement.objects.get(id=announcement_id)
                HousingEligibilityAnalysis.objects.update_or_create(
                    user_id=user_id,
                    announcement=announcement,
                    defaults={
                        'is_eligible': result['is_eligible'],
                        'priority': result['priority'],
                        'reasons': result.get('reasons', [])
                    }
                )
            except Exception as e:
                print(f"결과 저장 중 오류 발생 (공고 ID: {announcement_id}): {str(e)}")
                continue
        
    except Exception as e:
        print(f"자격 분석 중 오류 발생: {str(e)}")

class ProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")
        serializer.save(user=self.request.user)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 수정된 필드 확인
        modified_fields = set(request.data.keys())
        
        # 자격 분석에 영향을 주는 필드들
        eligibility_fields = {
            'birth_date', 'gender', 'university', 'graduate', 
            'employed', 'job_seeker', 'welfare_receipient',
            'parents_own_house', 'disability_in_family',
            'subscription_account', 'total_assets', 'car_value',
            'income_range'
        }

        # 자격 분석이 필요한 경우에만 실행
        if modified_fields & eligibility_fields:
            # 백그라운드에서 분석 시작
            thread = threading.Thread(
                target=analyze_eligibility_async,
                args=(request.user.id,)
            )
            thread.daemon = True
            thread.start()

        return Response(serializer.data)