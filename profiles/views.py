from rest_framework import generics, permissions
from .models import Profile
from .serializers import ProfileSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    # 로그인한 유저의 개인정보 조회 및 수정 
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}
    
    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user,
        defaults={ 
            "birth_date": "000000",  # 기본값
            "gender": "F",
            "university": False,
            "graduate": False,
            "employed": False,
            "job_seeker": False,
            "welfare_receipient": False,
            "parents_own_house": False,
            "disability_in_family": False,
            "subscription_account": 0,
            "total_assets": 0,
            "car_value": 0,
            "income_range": "100% 이하"
        })
        return profile