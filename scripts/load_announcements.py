# 프로젝트 루트/scripts/load_announcements.py
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

import os, json
from django.conf import settings
from announcements.models import Announcement, AnnouncementDocument

def run():
    print("▶️ 시작: 모든 문서(media)로 복사 및 DB 등록")

    data_root = os.path.join(settings.BASE_DIR, 'media', 'announcements')
    DOC_TYPES = [ t for t, _ in AnnouncementDocument.ANNOUNCE_TYPES ]

    for doc_type in DOC_TYPES:
        folder = os.path.join(data_root, doc_type)
        if not os.path.isdir(folder):
            print(f"  ⚠️ 폴더 없음: {folder}")
            continue

        for fname in os.listdir(folder):
            if not fname.endswith('.json'):
                continue

            path = os.path.join(folder, fname)
            with open(path, encoding='utf-8') as fp:
                data = json.load(fp)
            ann_id = data.get('announcement_id')
            if not ann_id:
                print(f"  ⚠️ announcement_id 없음: {fname}")
                continue

            ann = Announcement.objects.filter(id=ann_id).first()
            if not ann:
                print(f"  ⚠️ Announcement 미발견: id={ann_id}")
                continue

            doc, created = AnnouncementDocument.objects.get_or_create(
                announcement=ann,
                doc_type=doc_type,
            )
            # media/announcements/<doc_type>/ 아래로 복사
            doc.data_file.save(
                fname,
                open(path, 'rb'),
                save=True,
            )

            print(f"  ✅ [{doc_type}] {fname} → announcement={ann_id}")

    print("✅ load_announcements 완료!")
if __name__ == "__main__":
    run()
