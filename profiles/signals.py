from django.db.models.signals import post_save
from django.dispatch import receiver
from announcements.housing_eligibility_analyzer import analyze_user_eligibility
from announcements.models import Announcement, HousingEligibilityAnalysis
from .models import Profile
import os
from django.core.cache import cache

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    """
    프로필이 생성되거나 수정될 때 Celery 비동기 자격 분석을 실행
    """
    from .tasks import analyze_user_eligibility_task
    analyze_user_eligibility_task.delay(str(instance.user.id))

@receiver(post_save, sender=Profile)
def clear_eligibility_cache(sender, instance, created, **kwargs):
    """
    프로필이 수정되면 캐시된 자격 분석 결과를 삭제
    """
    cache_key = f'eligibility_analysis_{instance.user.id}'
    cache.delete(cache_key) 