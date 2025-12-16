# profiles/tasks.py
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
    time_limit=600,  # 10분으로 증가
)
def analyze_user_eligibility_task(user_id: int):
    """
    사용자의 모든 공고에 대한 자격 분석
    View에서 동기식으로 호출되므로 결과를 반환
    """
    logger.info(f"[CELERY] Task 시작 - user_id: {user_id}")

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist):
        error_msg = f"사용자 또는 프로필 존재하지 않음 - user_id: {user_id}"
        logger.error(f"[CELERY] {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'total': 0,
            'analyzed': 0,
            'eligible': 0
        }

    user_data = profile_to_user_data(profile)
    results = {}

    announcements = Announcement.objects.filter(status__in=['open', 'upcoming', 'closed'])
    total_count = announcements.count()
    done_count = 0
    eligible_count = 0
    skipped_429_count = 0
    error_count = 0

    logger.info(f"[CELERY] 분석 시작: {total_count}개 공고")

    for ann in announcements:
        notice_json = ann.ai_summary_json

        if not notice_json:
            done_count += 1
            continue

        try:
            result = analyzer.analyze_eligibility_with_ai(user_data, notice_json)

        except HTTPError as e:
            status = getattr(e.response, "status_code", None)

            # 429 Too Many Requests → 재시도 없이 건너뜀
            if status == 429:
                logger.warning(f"[CELERY] Groq API 429 - 공고 {ann.id} 스킵")
                skipped_429_count += 1
                done_count += 1
                continue

            # 다른 HTTPError
            logger.error(f"[CELERY] 공고 {ann.id} HTTPError: {str(e)}")
            error_count += 1
            done_count += 1
            continue

        except Exception as e:
            logger.error(f"[CELERY] 공고 {ann.id} 분석 실패: {str(e)}")
            error_count += 1
            done_count += 1
            continue

        # 정상 처리
        is_eligible = result.get("is_eligible", False)
        
        HousingEligibilityAnalysis.objects.update_or_create(
            user=user,
            announcement=ann,
            defaults={
                'is_eligible': is_eligible,
                'priority': result.get("priority", "해당없음"),
                'reasons': result.get("reasons", [])
            }
        )
        
        results[ann.id] = result
        
        if is_eligible:
            eligible_count += 1

        done_count += 1
        
        # 로그 (10개마다)
        if done_count % 10 == 0:
            logger.info(f"[CELERY] 진행: {done_count}/{total_count}")

    # 전체 요약 저장
    profile.is_eligible = any(r.get('is_eligible', False) for r in results.values())
    profile.priority_info = results
    profile.save(update_fields=['is_eligible', 'priority_info'])

    logger.info(f"[CELERY] 사용자 {user_id} 분석 완료")
    return {
        'success': True,
        'total': total_count,
        'analyzed': done_count,
        'eligible': eligible_count,
        'skipped_429': skipped_429_count,
        'errors': error_count
    }

