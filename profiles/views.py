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
from profiles.tasks import analyze_user_eligibility_task
from django.utils import timezone

class ProfileCreateView(generics.CreateAPIView):
    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("이미 개인정보가 등록되어 있습니다.")
        profile = serializer.save(user=self.request.user)
        # 비동기 분석만 트리거
        analyze_user_eligibility_task.delay(str(self.request.user.id))
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

        modified_fields = set(request.data.keys())
        eligibility_fields = {
            'birth_date', 'gender', 'university', 'graduate', 
            'employed', 'job_seeker', 'welfare_receipient',
            'parents_own_house', 'disability_in_family',
            'subscription_account', 'total_assets', 'car_value',
            'income_range'
        }
        if modified_fields & eligibility_fields:
            analyze_user_eligibility_task.delay(str(request.user.id))
        return Response(serializer.data)