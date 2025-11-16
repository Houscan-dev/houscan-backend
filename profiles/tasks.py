from celery import shared_task
from django.contrib.auth import get_user_model
import logging
from profiles.models import Profile
from announcements.models import Announcement
import django.core.cache as cache
from announcements.models import Announcement, HousingEligibilityAnalysis

User = get_user_model()
logger = logging.getLogger('celery.tasks')

@shared_task(queue='profile',time_limit=300)
def analyze_user_eligibility_task(user_id): 
    logger.info(f"Task started for user_id: {user_id}")
    try:
        try:
            lock_cache_key = f'processing_eligibility_{user_id}'
            try:
                user = User.objects.get(id=user_id)
                profile = Profile.objects.get(user=user)
            except (User.DoesNotExist, Profile.DoesNotExist):
                    logger.error(f"[CELERY] 사용자 ID {user_id}: User 또는 Profile을 찾을 수 없음")
                    return "User or Profile not found"

            # 수정 필요
            user_data = {
                "id": user.id,
                "age": profile.age, 
                "birth_date": profile.birth_date.strftime("%Y.%m.%d") if profile.birth_date else None,
                "is_married": profile.is_married,
                "residence": profile.residence,
                "university": profile.is_university_student, # 예시 필드명
                "graduate": profile.is_graduate, # 예시 필드명
                "employed": profile.is_employed, # 예시 필드명
                "job_seeker": profile.is_job_seeker, # 예시 필드명
                "welfare_receipient": profile.is_welfare_receipient, # 예시 필드명
                "parents_own_house": profile.parents_own_house, # 예시 필드명
                "disability_in_family": profile.disability_in_family, # 예시 필드명
                "subscription_account": profile.subscription_account_months, # 예시 필드명
                "total_assets": profile.total_assets, # 예시 필드명
                "car_value": profile.car_value, # 예시 필드명
                "income_range": profile.income_range_percent, # 예시 필드명
            }
            results = {}
            all_announcements = Announcement.objects.filter(status__in=['open', 'upcoming'])
            
            for ann in all_announcements:
                ai_summary = ann.ai_summary_json
                if not ai_summary:
                    continue
                try:
                    criteria_str = ai_summary.get("application_eligibility", "신청자격 정보 없음")
                    priority_data = ai_summary.get("priority_and_bonus", {})

                    # LLM 호출 1: 자격 판단
                    eligibility_result = HousingEligibilityAnalysis.check_eligibility_with_llm(
                        user_data, criteria_str, {}
                    )
                            
                    is_eligible = eligibility_result.get("is_eligible", False)
                    reasons = eligibility_result.get("reasons", [])
                    priority_str = None

                    # LLM 호출 2: 우선순위 판단 (자격 충족 시)
                    if is_eligible:
                        priority_result = HousingEligibilityAnalysis.check_priority_with_llm(
                            user_data, priority_data
                        )
                        priority_str = priority_result.get("priority", "판단 불가")
                            
                    # 4. results 딕셔너리에 결과 저장
                    results[ann.id] = {
                        'is_eligible': is_eligible,
                        'priority': priority_str or "해당없음", # None 대신 "해당없음" 저장
                        'reasons': reasons
                    }
                            
                except Exception as llm_e:
                    logger.error(f"[CELERY] 공고 {ann.id} LLM 분석 실패: {llm_e}")
                    results[ann.id] = {
                        'is_eligible': False,
                        'priority': "분석 오류",
                        'reasons': [f"LLM 분석 중 오류 발생: {str(llm_e)}"]
                    }
            logger.info(f"[CELERY] 분석 완료: {len(results)}개 공고 처리")
            saved_count = save_eligibility_results_to_db(user_id, results)
                    
            logger.info(f"[CELERY] 사용자 {user_id} 완료: {saved_count}개 항목 저장")
            return f"사용자 {user_id}의 {saved_count}개 공고 자격 분석 완료"
        
        finally:
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