# profiles/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from django.core.cache import cache
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from profiles.tasks import analyze_user_eligibility_task
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from announcements.models import Announcement
import logging

logger = logging.getLogger(__name__)


class ProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")

        # Profile 저장 (시그널 발동 안 함)
        profile = serializer.save(user=self.request.user)
        return profile

    def create(self, request, *args, **kwargs):
        """
        프로필 생성 + 자격 분석 (동기식)
        분석이 완료될 때까지 대기 후 응답
        """
        user_id = request.user.id
        
        # 1. 프로필 생성
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            profile = self.perform_create(serializer)
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
        
        logger.info(f"[VIEW] 프로필 생성 완료: User {user_id}")
        
        # 2. 자격 분석 (동기식 실행)
        try:
            logger.info(f"[VIEW] 자격 분석 시작: User {user_id}")
            
            # Celery task 실행 및 대기
            task = analyze_user_eligibility_task.apply_async(
                args=[user_id],
                queue='profile'
            )
            
            # 결과 대기 (최대 10분)
            result = task.get(timeout=600)
            
            logger.info(f"[VIEW] 자격 분석 완료: User {user_id} - {result}")
            
            # 분석 완료 후 프로필 다시 조회 (is_eligible, priority_info 업데이트됨)
            profile.refresh_from_db()
            
            return Response({
                'success': True,
                'message': '프로필 생성 및 자격 분석이 완료되었습니다.'
            }, status=201)
            
        except Exception as e:
            logger.error(f"[VIEW] 자격 분석 실패: User {user_id} - {e}")
            
            # 분석 실패해도 프로필은 저장된 상태
            return Response({
                'success': False,
                'message': '프로필은 생성되었으나 자격 분석에 실패했습니다.',
                'error': str(e),
                'profile': ProfileSerializer(profile).data
            }, status=201)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

    def patch(self, request, *args, **kwargs):
        """
        프로필 업데이트 + 자격 재분석 (동기식)
        분석이 완료될 때까지 대기 후 응답
        """
        user_id = request.user.id
        
        # 1. 프로필 업데이트
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # 시그널 발동 방지를 위해 update_fields 지정
        updated_profile = serializer.save()
        
        logger.info(f"[VIEW] 프로필 업데이트 완료: User {user_id}")
        
        # 2. 자격 재분석 (동기식 실행)
        try:
            logger.info(f"[VIEW] 자격 재분석 시작: User {user_id}")
            
            # Celery task 실행 및 대기
            task = analyze_user_eligibility_task.apply_async(
                args=[user_id],
                queue='profile'
            )
            
            # 결과 대기 (최대 10분)
            result = task.get(timeout=600)
            
            logger.info(f"[VIEW] 자격 재분석 완료: User {user_id} - {result}")
            
            # 분석 완료 후 프로필 다시 조회
            updated_profile.refresh_from_db()
            
            return Response({
                'success': True,
                'message': '프로필 업데이트 및 자격 재분석이 완료되었습니다.',
                'profile': ProfileSerializer(updated_profile).data,
                'analysis_summary': result
            }, status=200)
            
        except Exception as e:
            logger.error(f"[VIEW] 자격 재분석 실패: User {user_id} - {e}")
            
            # 분석 실패해도 프로필은 업데이트된 상태
            return Response({
                'success': False,
                'message': '프로필은 업데이트되었으나 자격 재분석에 실패했습니다.',
                'error': str(e),
                'profile': ProfileSerializer(updated_profile).data
            }, status=200)
    
    def get(self, request, *args, **kwargs):
        """
        프로필 조회 (분석 없음)
        """
        return super().get(request, *args, **kwargs)