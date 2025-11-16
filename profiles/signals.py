from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.core.cache import cache
from .tasks import analyze_user_eligibility_task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    user_id = instance.user.id
    lock_cache_key = f'processing_eligibility_{user_id}'

    # 중복 실행 방지 (이 로직이 핵심입니다)
    if cache.get(lock_cache_key):
        logger.info(f"Profile save signal for user {user_id}: Task already running or recently run. Skipping.")
        return
    # 1분간 잠금 설정
    cache.set(lock_cache_key, True, timeout=60)
    logger.info(f"Profile save signal for user {user_id}: Triggering analysis task.")
    
    # 비동기 태스크 실행
    analyze_user_eligibility_task.apply_async(
        args=[str(user_id)],
        queue='profile'
    )