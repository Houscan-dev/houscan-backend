import os, json, logging
from datetime import date, datetime
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def parse_ymd(s: str) -> date:
    # YYYY.MM.DD or YYYY-MM-DD 형식 문자열을 date 객체로 변환
    return datetime.strptime(s.replace('-', '.'), '%Y.%m.%d').date()

@shared_task(queue='status')
def update_announcements_status_from_json():
    from announcements.models import Announcement, AnnouncementDocument
    logger.info("▶▶▶ Task START: update_announcements_status_from_json")
    today = timezone.localdate()
    sched_dir = settings.MEDIA_ROOT / 'announcements' / 'schedule'

    for fname in os.listdir(sched_dir):
        if not fname.endswith('.json'):
            continue

        path = sched_dir / fname
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            ann_id = data.get("announcement_id")
            period = data.get("online_application_period", {})
            start_raw = period.get("start")
            end_raw = period.get("end")

            # 로그로 파악
            logger.info(f"📄 파일: {fname} → id: {ann_id}, start: {start_raw}, end: {end_raw}")

            if not ann_id or not start_raw or not end_raw:
                logger.warning(f"⚠️ 필수 정보 없음 → {fname}")
                continue

            start = parse_ymd(start_raw)
            end = parse_ymd(end_raw)
        except Exception as e:
            logger.error(f"❌ JSON 파싱 실패 {fname}: {e}")
            continue

        if today < start:
            status = 'upcoming'
        elif start <= today <= end:
            status = 'open'
        else:
            status = 'closed'

        try:
            ann = Announcement.objects.get(id=ann_id)
        except Announcement.DoesNotExist:
            logger.warning(f"❌ Announcement(id={ann_id}) 없음 → {fname}")
            continue

        # 상태 저장
        ann.posted_date = start
        ann.status = status
        ann.save()
        logger.info(f"✅ 상태 업데이트: {ann_id} → {status}, posted_date: {start}")

    logger.info("▶▶▶ Task END")
