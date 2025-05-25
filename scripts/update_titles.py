# scripts/update_titles_by_id.py

import os, json, django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "houscan.settings")
django.setup()

from announcements.models import Announcement

def run():
    mapping_path = BASE_DIR / "media" / "announcements" / "announcement_titles_by_id.json"
    with open(mapping_path, encoding="utf-8") as f:
        title_map = json.load(f)

    updated = 0
    for id_str, new_title in title_map.items():
        try:
            ann = Announcement.objects.get(id=int(id_str))
            ann.title = new_title
            ann.save()
            print(f"✅ ID {id_str} → {new_title}")
            updated += 1
        except Announcement.DoesNotExist:
            print(f"❌ ID {id_str} 없음")

    print(f"\n📦 총 {updated}건 title 업데이트 완료")
if __name__ == "__main__":
    run()
