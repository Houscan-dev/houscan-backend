from django.db.models.signals import post_save
from django.dispatch import receiver
from announcements.housing_eligibility_analyzer import process_users_eligibility
from announcements.models import Announcement, HousingEligibilityAnalysis
from .models import Profile
import os
from django.core.cache import cache

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    """
    프로필이 생성되거나 수정될 때 모든 공고에 대해 자격 분석을 실행
    """
    # 모든 공고 가져오기
    announcements = Announcement.objects.all()
    
    for announcement in announcements:
        try:
            # criteria 파일 가져오기
            criteria_doc = announcement.documents.get(doc_type="criteria")
            criteria_file = criteria_doc.data_file.path
            
            if os.path.exists(criteria_file):
                # 자격 분석 실행
                results = process_users_eligibility(criteria_file, user_ids=[str(instance.user.id)])
                user_result = results.get(f'user_{instance.user.id}')
                
                if user_result:
                    # 기존 분석 결과가 있으면 업데이트, 없으면 생성
                    analysis = HousingEligibilityAnalysis.objects.update_or_create(
                        user=instance.user,
                        announcement=announcement,
                        defaults={
                            'is_eligible': user_result['is_eligible'],
                            'priority': user_result['priority'],
                            'reasons': user_result.get('reasons', [])
                        }
                    )[0]  # update_or_create는 (object, created) 튜플을 반환

                    # 가장 최근 분석 결과로 프로필의 기본 자격 정보 업데이트
                    if analysis.is_eligible:
                        instance.is_eligible = True
                        instance.priority_info = {
                            'priority': analysis.priority,
                            'reasons': analysis.reasons
                        }
                        instance.save(update_fields=['is_eligible', 'priority_info'])
        except Exception as e:
            print(f"자격 분석 중 오류 발생 (공고 ID: {announcement.id}): {str(e)}")
            continue

@receiver(post_save, sender=Profile)
def clear_eligibility_cache(sender, instance, created, **kwargs):
    """
    프로필이 수정되면 캐시된 자격 분석 결과를 삭제
    """
    cache_key = f'eligibility_analysis_{instance.user.id}'
    cache.delete(cache_key) 