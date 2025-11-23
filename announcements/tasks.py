# announcements/tasks.py

import logging
from datetime import date
from typing import Optional
from django.utils import timezone
from celery import shared_task
from .models import Announcement

logger = logging.getLogger(__name__)

def parse_ymd_safe(s: str) -> Optional[date]:
    """
    YYYY.MM.DD 또는 YYYY-MM-DD 형식의 문자열을 date 객체로 변환합니다.
    (날짜 정보가 없거나 '미정'일 경우 None 반환)
    """
    if not s or '미정' in s:
        return None
    try:
        # YYYY.MM.DD 또는 YYYY-MM-DD 형식 지원
        return timezone.datetime.strptime(s.replace('-', '.'), '%Y.%m.%d').date()
    except (ValueError, TypeError):
        logger.warning(f"날짜 파싱 실패: '{s}'")
        return None

@shared_task(queue='status')
def update_announcements_status_from_ai_json():
    logger.info("▶▶▶ Task START: update_announcements_status_from_ai_json")
    today = timezone.localdate()
    
    # '마감'이 아닌 모든 공고를 가져와서 상태를 재검증합니다.
    announcements = Announcement.objects.exclude(status='closed')
    
    for ann in announcements:
        if not ann.ai_summary_json:
            logger.warning(f"⚠️ AI 요약본 없음 → {ann.id}: {ann.title} (상태 업데이트 스킵)")
            continue

        # --- [새로운 RAG 스키마 경로] ---
        try:
            # 1. schedule 객체에서 'online_application_period' 객체를 찾습니다.
            schedule_data = ann.ai_summary_json.get("application_schedule", {})
            period = schedule_data.get("online_application_period", {})
            
            # 2. 'start'와 'end' 날짜 문자열을 가져옵니다.
            start_raw = period.get("start")
            end_raw = period.get("end")
            
            # 3. 공고일도 가져옵니다.
            posted_date_raw = schedule_data.get("announcement_date")

        except Exception as e:
            logger.error(f"❌ JSON 스키마 파싱 실패 → {ann.id}: {ann.title} - {e}")
            continue
        # --- [경로 끝] ---

        if not start_raw or not end_raw:
            logger.warning(f"⚠️ 신청 기간 날짜 정보 없음 → {ann.id}: {ann.title}")
            continue

        start = parse_ymd_safe(start_raw)
        end = parse_ymd_safe(end_raw)
        announcement_date = parse_ymd_safe(posted_date_raw) or ann.announcement_date # 공고일이 없으면 기존 값 유지

        if not start or not end:
            logger.error(f"❌ 날짜 변환 실패 → {ann.id}: {ann.title} (start: {start_raw}, end: {end_raw})")
            continue

        # 3. status 결정
        new_status = ''
        if today < start:
            new_status = 'upcoming'
        elif start <= today <= end:
            new_status = 'open'
        else:
            new_status = 'closed'
        
        # 4. DB 업데이트 (변경된 경우에만)
        if ann.status != new_status or ann.announcement_date != announcement_date:
            ann.announcement_date = announcement_date
            ann.status = new_status
            ann.save(update_fields=['announcement_date', 'status'])
            logger.info(f"✅ 상태 업데이트: {ann.id} → {new_status}, announcement_date: {announcement_date}")

    logger.info("▶▶▶ Task END")