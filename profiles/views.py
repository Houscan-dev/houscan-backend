from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from django.core.cache import cache
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from profiles.tasks import analyze_user_eligibility_task
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from announcements.models import Announcement

class ProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")
        profile = serializer.save(user=self.request.user)

        # 분석 진행률 초기화
        total_announcements = Announcement.objects.filter(status__in=['open','upcoming']).count()
        cache.set(f"profile_analysis_progress_{self.request.user.id}", {
            "total": total_announcements,
            "done": 0
        }, timeout=3600)

        # Celery Task 실행
        analyze_user_eligibility_task.apply_async(
            args=[self.request.user.id],
            queue='profile'
        )

        return profile

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        progress = cache.get(f"profile_analysis_progress_{request.user.id}", {"total": 0, "done": 0})

        return Response({
            "profile": response.data,
            "eligibility_analysis_status": progress
        })



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
        
        response_data = serializer.data

        return Response(serializer.data)