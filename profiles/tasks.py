from celery import shared_task
from django.contrib.auth import get_user_model
from profiles.models import Profile
from announcements.models import Announcement, HousingEligibilityAnalysis
import analyzer
import logging
from django.core.cache import cache
from requests.exceptions import HTTPError

User = get_user_model()
logger = logging.getLogger('celery.tasks')


def profile_to_user_data(profile: Profile) -> dict:
    """Profile 모델을 analyzer.py에서 요구하는 JSON 구조로 변환"""
    return {
        "age": profile.age,
        "birth_date": profile.birth_date,
        "gender": profile.gender,
        "is_married": profile.is_married,
        "residence": profile.residence,
        "university": profile.university,
        "graduate": profile.graduate,
        "employed": profile.employed,
        "job_seeker": profile.job_seeker,
        "welfare_receipient": profile.welfare_receipient,
        "parents_own_house": profile.parents_own_house,
        "disability_in_family": profile.disability_in_family,
        "subscription_account": profile.subscription_account,
        "total_assets": profile.total_assets,
        "car_value": profile.car_value,
        "income_range": profile.income_range,
        "household_members": 1,
    }


@shared_task(
    queue='profile',
    time_limit=300,
)
def analyze_user_eligibility_task(user_id: int):
    logger.info(f"[CELERY] Task 시작 - user_id: {user_id}")
    lock_cache_key = f'processing_eligibility_{user_id}'

    # 락 없으면 종료 (시그널이 이미 막아줌)
    if not cache.get(lock_cache_key):
        logger.info(f"[CELERY] 락 없음 - 이미 처리됨 또는 중복 실행 방지됨 user_id={user_id}")
        return "Lock not found — already processed"

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist):
        logger.error(f"[CELERY] 사용자 또는 프로필 존재하지 않음 - user_id: {user_id}")
        cache.delete(lock_cache_key)
        return "User or Profile not found"

    user_data = profile_to_user_data(profile)
    results = {}

    announcements = Announcement.objects.filter(status__in=['open', 'upcoming','closed'])
    total_count = announcements.count()
    done_count = 0

    # 진행률 초기화
    progress_cache_key = f"profile_analysis_progress_{user.id}"
    cache.set(progress_cache_key, {"total": total_count, "done": done_count}, 3600)

    for ann in announcements:
        notice_json = ann.ai_summary_json

        if not notice_json:
            done_count += 1
            cache.set(progress_cache_key, {"total": total_count, "done": done_count})
            continue

        try:
            result = analyzer.analyze_eligibility_with_ai(user_data, notice_json)

        except HTTPError as e:
            status = getattr(e.response, "status_code", None)

            # 429 Too Many Requests → 재시도 없이 건너뜀
            if status == 429:
                logger.warning(f"[CELERY] Groq API 429 Too Many Requests - 공고 {ann.id} 스킵")
                done_count += 1
                cache.set(progress_cache_key, {"total": total_count, "done": done_count})
                continue

            # 다른 HTTPError는 기록만
            logger.error(f"[CELERY] 공고 {ann.id} HTTPError: {str(e)}")
            done_count += 1
            cache.set(progress_cache_key, {"total": total_count, "done": done_count})
            continue

        except Exception as e:
            logger.error(f"[CELERY] 공고 {ann.id} 분석 실패: {str(e)}")
            done_count += 1
            cache.set(progress_cache_key, {"total": total_count, "done": done_count})
            continue

        # 정상 처리
        HousingEligibilityAnalysis.objects.update_or_create(
            user=user,
            announcement=ann,
            defaults={
                'is_eligible': result.get("is_eligible", False),
                'priority': result.get("priority", "해당없음"),
                'reasons': result.get("reasons", [])
            }
        )
        results[ann.id] = result

        done_count += 1
        cache.set(progress_cache_key, {"total": total_count, "done": done_count})

    # 전체 요약 저장
    profile.is_eligible = any(r.get('is_eligible', False) for r in results.values())
    profile.priority_info = results
    profile.save(update_fields=['is_eligible', 'priority_info'])

    cache.delete(lock_cache_key)
    logger.info(f"[CELERY] 사용자 {user_id} {done_count}/{total_count} 공고 분석 완료")
    return f"[CELERY] 사용자 {user_id} {done_count}/{total_count} 공고 분석 완료"
