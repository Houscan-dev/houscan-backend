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
    
    # 태스크 내부에서의 저장인지 확인
    update_fields = kwargs.get('update_fields')
    if update_fields is not None:
        # update_fields가 지정된 경우 (태스크 내부 저장)
        # is_eligible, priority_info만 업데이트하는 경우 스킵
        if set(update_fields) == {'is_eligible', 'priority_info'}:
            logger.info(f"Profile save signal for user {user_id}: Internal task update. Skipping.")
            return
    
    lock_cache_key = f'processing_eligibility_{user_id}'

    # 중복 실행 방지
    lock_set = cache.add(lock_cache_key, True, timeout=60)
    
    if not lock_set:
        logger.info(f"Profile save signal for user {user_id}: Task already running or recently run. Skipping. (Lock Acquire Failed)")
        return
    
    logger.info(f"Profile save signal for user {user_id}: Lock successfully acquired. Queuing task.")
    
    analyze_user_eligibility_task.apply_async(
        args=[str(user_id)],
        queue='profile',
    )
    logger.info(f"Profile {'created' if created else 'updated'} for user {user_id}: Eligibility analysis task queued.")