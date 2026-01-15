# announcements/tasks.py

import logging
import re
from datetime import date, datetime
from typing import Optional, Tuple
from django.utils import timezone
from celery import shared_task
from .models import Announcement

logger = logging.getLogger(__name__)


def parse_ymd_safe(s: str) -> Optional[date]:
    """
    다양한 날짜 형식을 date 객체로 변환
    - YYYY.MM.DD 또는 YYYY-MM-DD
    - YYYY.M.D (한 자리 월/일)
    - YYYY.MM.DD. HH:MM (시간 포함)
    - YYYY.M.D.(요일) (요일 포함)
    """
    if not s or '미정' in s:
        return None
    
    try:
        # 괄호와 요일 제거: (월), (수) 등
        s = re.sub(r'\([^)]*\)', '', s)
        
        # 시간 정보 제거: HH:MM
        s = re.sub(r'\s*\d{1,2}:\d{2}.*$', '', s)
        
        # 공백 제거
        s = s.strip().rstrip('.')
        
        if not s:
            return None
        
        # - 를 . 으로 통일
        s = s.replace('-', '.')
        
        # 날짜 파싱 시도
        # YYYY.M.D 형식도 처리
        for fmt in ['%Y.%m.%d', '%Y.%-m.%-d', '%Y.%m.%d.']:
            try:
                return datetime.strptime(s, fmt).date()
            except (ValueError, AttributeError):
                continue
        
        # 마지막 시도: 점으로 분리해서 직접 파싱
        parts = s.split('.')
        if len(parts) >= 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return date(year, month, day)
        
        logger.warning(f"날짜 파싱 실패: '{s}'")
        return None
        
    except (ValueError, TypeError, IndexError) as e:
        logger.warning(f"날짜 파싱 실패: '{s}' - {e}")
        return None


def parse_period_safe(s: str) -> Tuple[Optional[date], Optional[date]]:
    """
    "YYYY.MM.DD. ~ YYYY.MM.DD." 형태의 문자열을 (start, end)로 변환
    연도가 생략된 경우 시작 날짜의 연도 사용
    """
    if not s or '미정' in s:
        return None, None

    try:
        parts = s.split('~')
        if len(parts) != 2:
            return None, None

        start_raw = parts[0].strip()
        end_raw = parts[1].strip()

        start = parse_ymd_safe(start_raw)
        
        # 종료일에 연도가 없는 경우 처리
        if start and end_raw and not re.match(r'\d{4}', end_raw):
            # 시작 날짜의 연도 사용
            year = start.year
            # 월.일 형식 추출
            end_raw_cleaned = re.sub(r'\([^)]*\)', '', end_raw)
            end_raw_cleaned = re.sub(r'\s*\d{1,2}:\d{2}.*$', '', end_raw_cleaned)
            end_raw_cleaned = end_raw_cleaned.strip().rstrip('.')
            
            parts_end = end_raw_cleaned.split('.')
            if len(parts_end) >= 2:
                month = int(parts_end[0])
                day = int(parts_end[1])
                end = date(year, month, day)
            else:
                end = parse_ymd_safe(end_raw)
        else:
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
    
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for ann in announcements:
        if not ann.ai_summary_json:
            logger.debug(f"⚠️ AI 요약본 없음 → {ann.id}: {ann.title}")
            skipped_count += 1
            continue

        try:
            schedule_data = ann.ai_summary_json.get("application_schedule", {})
            period_raw = schedule_data.get("online_application_period")
            posted_date_raw = schedule_data.get("announcement_date")
        except Exception as e:
            logger.error(f"❌ JSON 스키마 파싱 실패 → {ann.id}: {ann.title} - {e}")
            error_count += 1
            continue

        if not period_raw:
            logger.debug(f"⚠️ 신청 기간 없음 → {ann.id}: {ann.title}")
            skipped_count += 1
            continue

        start, end = parse_period_safe(period_raw)
        announcement_date = parse_ymd_safe(posted_date_raw) or ann.announcement_date

        if not start or not end:
            logger.warning(f"❌ 날짜 변환 실패 → {ann.id}: {ann.title} (raw: {period_raw})")
            error_count += 1
            continue

        if today < start:
            new_status = 'upcoming'
        elif start <= today <= end:
            new_status = 'open'
        else:
            new_status = 'closed'

        if ann.status != new_status or ann.announcement_date != announcement_date:
            old_status = ann.status
            ann.status = new_status
            ann.announcement_date = announcement_date
            ann.save(update_fields=['status', 'announcement_date'])
            logger.info(f"✅ 상태 업데이트: {ann.id} ({old_status} → {new_status})")
            updated_count += 1

    logger.info(f"▶▶▶ Task END: 업데이트={updated_count}, 스킵={skipped_count}, 에러={error_count}")