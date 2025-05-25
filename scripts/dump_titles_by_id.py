# scripts/extract_titles_from_schedule.py

import os
import sys
import json
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "houscan.settings")
django.setup()

from announcements.models import Announcement

def run():
    input_dir = BASE_DIR / "media" / "announcements" / "schedule"
    output_path = BASE_DIR / "media" / "announcements" / "announcement_titles_by_id.json"
    os.makedirs(output_path.parent, exist_ok=True)

    data = {}
    for file in input_dir.glob("*.json"):
        try:
            with open(file, encoding="utf-8") as f:
                content = json.load(f)

            ann_id = content.get("announcement_id")
            if not ann_id:
                print(f"⚠️  {file.name}: 'announcement_id' 없음")
                continue

            try:
                ann = Announcement.objects.get(id=ann_id)
                data[str(ann_id)] = ann.title
                print(f"✅ {file.name} → ID {ann_id} → {ann.title}")
            except Announcement.DoesNotExist:
                print(f"❌ ID {ann_id} 에 해당하는 Announcement 없음")

        except Exception as e:
            print(f"❌ {file.name} 읽기 실패: {e}")

    if data:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n📄 총 {len(data)}건 저장 완료 → {output_path}")
    else:
        print("🚫 저장할 데이터가 없습니다.")
if __name__ == "__main__":
    run()