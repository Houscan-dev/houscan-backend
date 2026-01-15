# announcements/tasks.py

import logging
from datetime import date
from typing import Optional, Tuple
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
        return timezone.datetime.strptime(s.replace('-', '.').rstrip('.'), '%Y.%m.%d').date()
    except (ValueError, TypeError):
        logger.warning(f"날짜 파싱 실패: '{s}'")
        return None


def parse_period_safe(s: str) -> Tuple[Optional[date], Optional[date]]:
    """
    "YYYY.MM.DD. ~ YYYY.MM.DD." 형태의 문자열을 (start, end)로 변환
    """
    if not s or '미정' in s:
        return None, None

    try:
        parts = s.split('~')
        if len(parts) != 2:
            return None, None

        start_raw = parts[0].strip().rstrip('.')
        end_raw = parts[1].strip().rstrip('.')

        start = parse_ymd_safe(start_raw)
        end = parse_ymd_safe(end_raw)

        return start, end
    except Exception as e:
        logger.warning(f"기간 파싱 실패: '{s}' - {e}")
        return None, None


@shared_task(queue='status')
def update_announcements_status_from_ai_json():
    logger.info("▶▶▶ Task START: update_announcements_status_from_ai_json")
    today = timezone.localdate()

    announcements = Announcement.objects.exclude(status='closed')

    for ann in announcements:
        if not ann.ai_summary_json:
            logger.warning(f"⚠️ AI 요약본 없음 → {ann.id}: {ann.title} (상태 업데이트 스킵)")
            continue

        try:
            schedule_data = ann.ai_summary_json.get("application_schedule", {})
            period_raw = schedule_data.get("online_application_period")
            posted_date_raw = schedule_data.get("announcement_date")
        except Exception as e:
            logger.error(f"❌ JSON 스키마 파싱 실패 → {ann.id}: {ann.title} - {e}")
            continue

        if not period_raw:
            logger.warning(f"⚠️ 신청 기간 없음 → {ann.id}: {ann.title}")
            continue

        start, end = parse_period_safe(period_raw)
        announcement_date = parse_ymd_safe(posted_date_raw) or ann.announcement_date

        if not start or not end:
            logger.error(f"❌ 날짜 변환 실패 → {ann.id}: {ann.title} (raw: {period_raw})")
            continue

        if today < start:
            new_status = 'upcoming'
        elif start <= today <= end:
            new_status = 'open'
        else:
            new_status = 'closed'

        if ann.status != new_status or ann.announcement_date != announcement_date:
            ann.status = new_status
            ann.announcement_date = announcement_date
            ann.save(update_fields=['status', 'announcement_date'])
            logger.info(f"✅ 상태 업데이트: {ann.id} → {new_status}, announcement_date: {announcement_date}")

    logger.info("▶▶▶ Task END")
