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
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class ProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")
        return serializer.save(user=self.request.user,eligibility_status='running')

    def create(self, request, *args, **kwargs):
        user_id = request.user.id
    
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

        # 비동기 분석 시작 
        analyze_user_eligibility_task.delay(user_id)
        logger.info(f"[VIEW] 자격 분석 task 비동기 요청: User {user_id}")

        return Response(
            {
                'success': True,
                'message': '프로필이 생성되었고 자격 분석이 시작되었습니다.',
                'profile': ProfileSerializer(profile).data,
            },
            status=201
        )
        


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

    def patch(self, request, *args, **kwargs):
        user_id = request.user.id
        profile = self.get_object()
        if profile.eligibility_status == 'running':
            return Response(
                {
                    'success': False,
                    'message': '자격 분석이 이미 진행 중입니다.',
                    'eligibility_status': profile.eligibility_status,
                },
                status=409
            )

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"[VIEW] 프로필 업데이트 완료: User {user_id}")
        
        profile.eligibility_status = 'running'
        profile.save(update_fields=['eligibility_status'])

        analyze_user_eligibility_task.delay(user_id)
        logger.info(f"[VIEW] 자격 재분석 task 비동기 요청: User {user_id}")

        return Response(
            {
                'success': True,
                'message': '프로필이 수정되었고 자격 재분석이 시작되었습니다.',
                'profile': ProfileSerializer(profile).data,
            },
            status=200
        )
            
    
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        return Response({
            'success': True,
            'profile': ProfileSerializer(profile).data,
            
        }, status=200)
    