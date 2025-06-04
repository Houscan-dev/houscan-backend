from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.core.cache import cache
from .tasks import analyze_user_eligibility_task

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    # 프로필이 생성되거나 수정될 때 Celery 비동기 자격 분석을 실행
    cache_key = f'processing_eligibility_{instance.user.id}'
    if cache.get(cache_key):
        return
    
    cache.set(cache_key, True, timeout=60)  # 1분간 중복 실행 방지
    
    try:
        eligibility_cache_key = f'eligibility_analysis_{instance.user.id}'
        cache.delete(eligibility_cache_key) # 기존 캐시 삭제
        analyze_user_eligibility_task.delay(str(instance.user.id)) # 태스크 실행
    finally:
        cache.delete(cache_key)