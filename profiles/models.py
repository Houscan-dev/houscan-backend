from django.db import models
from django.conf import settings
from datetime import datetime, date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from announcements.models import Announcement, HousingEligibilityAnalysis
import os
from announcements.housing_eligibility_analyzer import analyze_user_eligibility
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    birth_date = models.CharField(max_length=6)
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성')])
    university = models.BooleanField() 
    graduate = models.BooleanField()
    employed = models.BooleanField()
    job_seeker = models.BooleanField()
    welfare_receipient = models.BooleanField()
    parents_own_house = models.BooleanField()
    disability_in_family = models.BooleanField()
    subscription_account = models.IntegerField()
    total_assets = models.BigIntegerField()
    car_value = models.BigIntegerField()
    income_range = models.CharField(max_length=20, choices=[('100% 이하', '100% 이하'),('50% 이하', '50% 이하')])
    is_eligible = models.BooleanField(null=True, blank=True)
    priority_info = models.JSONField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

    @property
    def age(self):
        try:
            birth = datetime.strptime(self.birth_date, "%y%m%d").date()
            today = date.today()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return None

    def __str__(self):
        return f"{self.user.email}'s profile"

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    """
    프로필이 생성되거나 수정될 때 모든 공고에 대해 자격 분석을 실행
    """
    # 모든 공고 가져오기
    announcements = Announcement.objects.all()
    
    for announcement in announcements:
        try:
            # criteria 파일 가져오기
            criteria_doc = announcement.documents.get(doc_type="criteria")
            criteria_file = criteria_doc.data_file.path
            
            if os.path.exists(criteria_file):
                # 자격 분석 실행
                results = analyze_user_eligibility(str(instance.user.id))
                user_result = results.get(str(announcement.id))
                
                if user_result:
                    # 기존 분석 결과가 있으면 업데이트, 없으면 생성
                    analysis = HousingEligibilityAnalysis.objects.update_or_create(
                        user=instance.user,
                        announcement=announcement,
                        defaults={
                            'is_eligible': user_result['is_eligible'],
                            'priority': user_result['priority'],
                            'reasons': user_result.get('reasons', []),
                            'analyzed_at': timezone.now()
                        }
                    )[0]  # update_or_create는 (object, created) 튜플을 반환

                    # 가장 최근 분석 결과로 프로필의 기본 자격 정보 업데이트
                    if analysis.is_eligible:
                        instance.is_eligible = True
                        instance.priority_info = {
                            'priority': analysis.priority,
                            'reasons': analysis.reasons
                        }
                        instance.save(update_fields=['is_eligible', 'priority_info'])
        except Exception as e:
            print(f"자격 분석 중 오류 발생 (공고 ID: {announcement.id}): {str(e)}")
            continue


