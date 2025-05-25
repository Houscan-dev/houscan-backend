import os, json, logging
from datetime import date, datetime
from celery import shared_task
from django.conf import settings
from .models import Announcement, AnnouncementDocument
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
    sched_dir = settings.MEDIA_ROOT / 'announcements' /'schedule'

    for fname in os.listdir(sched_dir):
        if not fname.endswith('.json'):
            continue

        path = sched_dir / fname
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            ann_id = data.get("announcement_id")
            period = data.get("online_application_period", {})
            start = parse_ymd(period.get("start"))
            end   = parse_ymd(period.get("end"))
            if not ann_id or not start or not end:
                logger.warning(f"⚠️ 필수 정보 없음 → {fname}")
                continue
        except Exception as e:
            logger.error(f"  → JSON 파싱 실패 {fname}: {e}")
            continue

        if today < start:
            status = 'upcoming'
        elif start <= today <= end:
            status = 'open'
        else:
            status = 'closed'

        ann = Announcement.objects.get(id=ann_id)
        ann.posted_date = start
        ann.status = status
        ann.save()

    logger.info("▶▶▶ Task END")