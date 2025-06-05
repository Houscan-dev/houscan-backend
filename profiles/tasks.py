from celery import shared_task
from django.contrib.auth import get_user_model
from .models import HousingEligibilityAnalysis, Announcement
import logging

User = get_user_model()
logger = logging.getLogger('celery.tasks')
import django.core.cache as cache

@shared_task(queue='profile',time_limit=300)
def analyze_user_eligibility_task(user_id):
    logger.info(f"Task started for user_id: {user_id}")
    try:
        from announcements.housing_eligibility_analyzer import analyze_user_eligibility
        lock_cache_key = f'processing_eligibility_{user_id}'
        if cache.get(lock_cache_key):
            logger.warning(f"Task already running for user {user_id}")
            return "Task already running"
        cache.set(lock_cache_key, True, timeout=300) 
        try:
            results = analyze_user_eligibility(user_id)
            logger.info(f"[CELERY] 분석 완료: {len(results)}개 공고 처리")
            saved_count = save_eligibility_results_to_db(user_id, results)
            logger.info(f"[CELERY] 사용자 {user_id} 완료: {saved_count}개 항목 저장")
            return f"사용자 {user_id}의 {saved_count}개 공고 자격 분석 완료"
        finally:
            # 락 해제
            cache.delete(lock_cache_key)
        
    except Exception as e:
        logger.error(f"[CELERY] 사용자 {user_id} 분석 실패: {str(e)}")
        raise

def save_eligibility_results_to_db(user_id: str, results: dict):
    """
    분석 결과를 HousingEligibilityAnalysis 모델에 저장
    """
    try:
        user = User.objects.get(id=user_id)
        saved_count = 0
        
        for announcement_id, result in results.items():
            try:
                announcement = Announcement.objects.get(id=announcement_id)
                
                # 기존 데이터가 있으면 업데이트, 없으면 생성
                obj, created = HousingEligibilityAnalysis.objects.update_or_create(
                    user=user,
                    announcement=announcement,
                    defaults={
                        'is_eligible': result['is_eligible'],
                        'priority': result['priority'],
                        'reasons': result['reasons']
                    }
                )
                
                saved_count += 1
                
            except Announcement.DoesNotExist:
                logger.warning(f"[CELERY] 공고 ID {announcement_id}: 존재하지 않음")
                continue
            except Exception as e:
                logger.error(f"[CELERY] 공고 ID {announcement_id}: 저장 실패 - {str(e)}")
                continue
        
        return saved_count
        
    except User.DoesNotExist:
        logger.error(f"[CELERY] 사용자 ID {user_id}: 존재하지 않음")
        raise
    except Exception as e:
        logger.error(f"[CELERY] DB 저장 실패: {str(e)}")
        raise