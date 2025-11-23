from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.core.cache import cache
from .tasks import analyze_user_eligibility_task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Profile, dispatch_uid="profile_post_save_unique")
def analyze_eligibility(sender, instance, created, **kwargs):
    user_id = instance.user.id
    lock_cache_key = f'processing_eligibility_{user_id}'
    
    # 중복 실행 방지
    if not cache.add(lock_cache_key, True, timeout=60):
        logger.info(f"Profile save signal for user {user_id}: Task already running or recently run. Skipping.")
        return
    
    # 비동기 태스크 실행
    analyze_user_eligibility_task.apply_async(
        args=[str(user_id)],
        queue='profile',
        countdown=1
    )
    logger.info(f"Profile {'created' if created else 'updated'} for user {user_id}: Eligibility analysis task queued.")