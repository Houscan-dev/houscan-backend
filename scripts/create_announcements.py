# scripts/create_announcements.py
import os
import sys
import django
from pathlib import Path

# 프로젝트 루트 경로 등록
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'houscan.settings')
django.setup()

import os
from django.conf import settings
from announcements.models import Announcement, AnnouncementDocument
import re

def run():
    """
    ① data 폴더의 각 doc_type 서브폴더에서
       '*_<doc_type>.json' 파일들을 스캔해,
       base 이름(‘1_행복주택’ 같은)으로 Announcement를 생성합니다.
    """
    DATA_ROOT = os.path.join(settings.BASE_DIR, 'media', 'announcements')
    # AnnouncementDocument.ANNOUNCE_TYPES 에 있는 doc_type 들만 사용
    doc_types = [t for t, _ in AnnouncementDocument.ANNOUNCE_TYPES]
    bases = set()

    # 모든 doc_type 폴더를 순회하며 base 집합 수집
    for dt in doc_types:
        folder = os.path.join(DATA_ROOT, dt)
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            if fname.endswith(f'_{dt}.json'):
                base = fname.rsplit(f'_{dt}.json', 1)[0]
                bases.add(base)

    print(f"▶️ {len(bases)}개의 Announcement 생성 시도")
    for base in sorted(bases):
        ann, created = Announcement.objects.get_or_create(
            title=base,
            defaults={
                'posted_date': '2025-01-01',
                'status': 'upcoming',
            }
        )
        print(f"  {'✅ 생성' if created else '🔄 존재'}: {ann.id} · {base}")
    print("✅ 모든 Announcement 준비 완료!")
if __name__ == "__main__":
    run()
