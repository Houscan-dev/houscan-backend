import os
import sys
import json
import django
import unicodedata

# Django 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'houscan.settings')
django.setup()

from announcements.models import Announcement

def update_announcements_from_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated, skipped, not_found = 0, 0, 0

    for str_id, entry in data.items():
        try:
            ann_id = int(str_id)
            old_title = entry.get("old_title", "").strip()
            new_title = entry.get("new_title", "").strip()
            pdf_name  = entry.get("pdf", "").strip()

            ann = Announcement.objects.get(id=ann_id)
            print(f"Comparing: DB='{ann.title.strip()}', JSON='{old_title}'")
            db_title_norm = unicodedata.normalize('NFC', ann.title.strip())
            old_title_norm = unicodedata.normalize('NFC', old_title)

            if db_title_norm == old_title_norm:
                ann.title = new_title
                updated += 1
            else:
                print(f"⚠️  ID {ann_id} - 제목 불일치: 현재='{db_title_norm}', 기대='{old_title_norm}'")
                skipped += 1

            ann.pdf_name = pdf_name
            ann.save()
            print(f"✔️  ID {ann_id} 업데이트 완료")

        except Announcement.DoesNotExist:
            print(f"❌  ID {str_id} 존재하지 않음")
            not_found += 1

    print("\n📊 결과 요약:")
    print(f"  🔄 업데이트 완료: {updated}")
    print(f"  ⚠️  제목 불일치로 건너뜀: {skipped}")
    print(f"  ❌ 존재하지 않는 ID: {not_found}")


if __name__ == "__main__":
    json_file_path = "scripts/data/announcement_title_update_map.json"
    update_announcements_from_json(json_file_path)
