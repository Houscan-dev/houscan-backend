from rest_framework import generics, permissions
from .models import Profile
from .serializers import ProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

class ProfileCreateView(generics.CreateAPIView):
    # 로그인한 유저의 개인정보 조회 및 수정 
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