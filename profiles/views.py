from rest_framework import generics, permissions
from .models import Profile
from .serializers import ProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
import threading
from announcements.housing_eligibility_analyzer import analyze_user_eligibility
from announcements.models import Announcement, HousingEligibilityAnalysis
from django.utils import timezone


class ProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")
        profile = serializer.save(user=self.request.user)
        
        # 프로필 생성 후 자격 분석 실행
        try:
            # 자격 분석 실행
            user_id = str(self.request.user.id)
            print(f"자격 분석 시작 - 사용자 ID: {user_id}")
            
            results = analyze_user_eligibility(user_id)
            print(f"자격 분석 결과: {results}")
            
            if results:
                # 결과 저장
                for announcement_id, result in results.items():
                    try:
                        announcement = Announcement.objects.get(id=announcement_id)
                        analysis = HousingEligibilityAnalysis.objects.create(
                            user=self.request.user,
                            announcement=announcement,
                            is_eligible=result['is_eligible'],
                            priority=result['priority'],
                            reasons=result.get('reasons', []),
                            analyzed_at=timezone.now()
                        )
                        print(f"새로운 분석 결과 저장 완료: 공고 ID {announcement_id}")
                    except Exception as e:
                        print(f"결과 저장 중 오류 발생 (공고 ID: {announcement_id}): {str(e)}")
                        continue
        except Exception as e:
            print(f"자격 분석 중 오류 발생: {str(e)}")
        
        return profile


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
        print(f"수정된 필드: {modified_fields}")
        
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
            print("자격 분석이 필요한 필드가 수정되었습니다.")
            try:
                # 기존 분석 결과 삭제
                HousingEligibilityAnalysis.objects.filter(user=request.user).delete()
                print("기존 분석 결과 삭제 완료")
                
                # 수정된 프로필 정보로 자격 분석 실행
                user_id = str(request.user.id)
                print(f"자격 분석 시작 - 사용자 ID: {user_id}")
                
                # 자격 분석 실행
                results = analyze_user_eligibility(user_id)
                print(f"자격 분석 결과: {results}")
                
                if not results:
                    print("자격 분석 결과가 없습니다.")
                    return Response(serializer.data)
                
                # 결과 저장
                for announcement_id, result in results.items():
                    try:
                        announcement = Announcement.objects.get(id=announcement_id)
                        analysis = HousingEligibilityAnalysis.objects.create(
                            user=request.user,
                            announcement=announcement,
                            is_eligible=result['is_eligible'],
                            priority=result['priority'],
                            reasons=result.get('reasons', []),
                            analyzed_at=timezone.now()
                        )
                        print(f"새로운 분석 결과 저장 완료: 공고 ID {announcement_id}")
                    except Exception as e:
                        print(f"결과 저장 중 오류 발생 (공고 ID: {announcement_id}): {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"자격 분석 중 오류 발생: {str(e)}")

        return Response(serializer.data)