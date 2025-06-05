from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.core.cache import cache
from .tasks import analyze_user_eligibility_task

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    # 자격에 영향을 주는 필드 체크
    eligibility_fields = {
        'birth_date', 'gender', 'university', 'graduate', 
        'employed', 'job_seeker', 'welfare_receipient',
        'parents_own_house', 'disability_in_family',
        'subscription_account', 'total_assets', 'car_value',
        'income_range'
    }
    
    # 새로 생성된 경우는 무조건 실행
    if created:
        should_analyze = True
    else:
        # 수정된 경우, 이전 값과 비교
        try:
            old_instance = Profile.objects.get(pk=instance.pk)
            should_analyze = any(
                getattr(instance, field) != getattr(old_instance, field)
                for field in eligibility_fields
            )
        except Profile.DoesNotExist:
            should_analyze = True
    
    if should_analyze:
        user_id = instance.user.id
        lock_cache_key = f'processing_eligibility_{user_id}'
        
        # 중복 실행 방지
        if cache.get(lock_cache_key):
            return
            
        cache.set(lock_cache_key, True, timeout=60)
        
        # 비동기 태스크 실행
        analyze_user_eligibility_task.apply_async(
            args=[str(user_id)],
            queue='profile'
        )