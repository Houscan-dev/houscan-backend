from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.core.cache import cache
from .tasks import analyze_user_eligibility_task

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    user_id = instance.user.id
    lock_cache_key = f'processing_eligibility_{user_id}'
    result_cache_key = f'eligibilityanalysis{user_id}'
    print("Signal received for Profile save")
    print(f"user id: {instance.user.id if instance.user else 'No user'}")

    # 1분 지나기 전 중복 실행 방지
    if cache.get(lock_cache_key):
        return
    cache.set(lock_cache_key, True, timeout=60)

    # Celery 태스크 실행
    analyze_user_eligibility_task.apply_async(args=[str(user_id)], queue='profile')

    # 수정일 경우 캐시 삭제
    if not created:
        cache.delete(result_cache_key)
