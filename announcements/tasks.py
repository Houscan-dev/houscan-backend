import os, json, logging
from datetime import date, datetime
from celery import shared_task
from django.conf import settings
from .models import Announcement
from django.utils import timezone

logger = logging.getLogger(__name__)

def parse_ymd(s: str) -> date:
    """
    "YYYY.MM.DD" or "YYYY-MM-DD" 형식 문자열을 date 객체로 변환
    """
    return datetime.strptime(s.replace('-', '.'), '%Y.%m.%d').date()

@shared_task
def update_announcements_status_from_json():
    logger.info("▶▶▶ Task START: update_announcements_status_from_json")
    today = timezone.localdate()
    sched_dir = settings.ANNOUNCEMENTS_JSON_ROOT / 'schedule'
    logger.info(f"▶▶▶ Looking in {sched_dir}")

    if not sched_dir.is_dir():
        logger.warning(f"▶▶▶ schedule 디렉터리 없음: {sched_dir}")
        return
    
    for fname in os.listdir(sched_dir):
        if not fname.lower().endswith('.json'):
            continue
        path = sched_dir / fname
        logger.info(f"▶▶▶ Processing file: {path}")
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            start_s = data['online_application_period']['start']
            end_s   = data['online_application_period']['end']
            if not start_s or not end_s:
                logger.info(f"  → 기간 정보 없음, 건너뜀: {fname}")
                continue
            start = parse_ymd(start_s)
            end   = parse_ymd(end_s)
        except Exception as e:
            logger.error(f"  → JSON 파싱 실패 {fname}: {e}")
            continue

        if today < start:
            status = 'upcoming'
        elif start <= today <= end:
            status = 'open'
        else:
            status = 'closed'

        obj, created = Announcement.objects.update_or_create(
            file_name=f"schedule/{fname}",
            defaults={
                'posted_date': start,
                'status': status
            }
        )
        logger.info(f"  → {'Created' if created else 'Updated'}: {obj.file_name} → {obj.status}")

    logger.info("▶▶▶ Task END")