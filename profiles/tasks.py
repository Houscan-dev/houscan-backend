# profiles/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from profiles.models import Profile
from announcements.models import Announcement, HousingEligibilityAnalysis
import analyzer
import logging
from requests.exceptions import HTTPError

User = get_user_model()
logger = logging.getLogger('celery.tasks')


def profile_to_user_data(profile: Profile) -> dict:
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


@shared_task(bind=True, queue='profile')
def analyze_user_eligibility_task(self, user_id: int):
    logger.info(f"[CELERY] 자격 분석 시작 - user_id={user_id}")

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)

        # 상태: running
        profile.eligibility_status = 'running'
        profile.save(update_fields=['eligibility_status'])

        user_data = profile_to_user_data(profile)
        results = {}

        announcements = Announcement.objects.filter(
            status__in=['open', 'upcoming', 'closed']
        )

        for ann in announcements:
            notice_json = ann.ai_summary_json
            if not notice_json:
                continue

            try:
                # announcement 단위 예외 처리
                result = analyzer.analyze_eligibility_with_ai(
                    user_data, notice_json
                )
            except Exception as e:
                logger.warning(
                    f"[CELERY] AI 분석 실패 - user={user_id}, ann={ann.id}: {e}"
                )
                continue 

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

        #결과요약
        profile.is_eligible = any(
            r.get('is_eligible', False) for r in results.values()
        )
        profile.priority_info = results

        profile.eligibility_status = 'done'
        profile.save(update_fields=[
            'is_eligible',
            'priority_info',
            'eligibility_status'
        ])

        logger.info(f"[CELERY] 자격 분석 완료 - user_id={user_id}")

    except Exception as e:
        # 실패 상태 남김
        logger.exception(f"[CELERY] 전체 분석 실패 - user_id={user_id}")
        if 'profile' in locals():
            profile.eligibility_status = 'error'
            profile.save(update_fields=['eligibility_status'])

        return
