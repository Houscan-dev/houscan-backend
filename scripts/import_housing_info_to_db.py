import os
import sys
import json
import django
from pathlib import Path

# 프로젝트 루트 경로 등록
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "houscan.settings")
django.setup()

from announcements.models import Announcement, HousingInfo

HOUSING_INFO_DIR = "media/announcements/housing_info"

def load_housing_info_to_db():
    for fname in os.listdir(HOUSING_INFO_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(HOUSING_INFO_DIR, fname)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        announcement_id = data.get("announcement_id")
        housing_list = data.get("housing_info", [])

        try:
            ann = Announcement.objects.get(id=announcement_id)
        except Announcement.DoesNotExist:
            print(f"❌ Announcement ID {announcement_id} 없음 → 건너뜀")
            continue

        for h in housing_list:
            ext_id = h.get("id")
            # 중복 방지 (재실행 대비)
            if HousingInfo.objects.filter(announcement=ann).exists():
                continue

            HousingInfo.objects.create(
                announcement=ann,
                name=h.get("name"),
                address=h.get("address"),
                district = h.get("district"),
                total_households=h.get("total_households"),
                supply_households=h.get("supply_households"),
                type=h.get("type"),
                house_type=h.get("house_type"),
                elevator=h.get("elevator"),
                parking=h.get("parking"),
            )

        print(f"✅ {fname} → {len(housing_list)}개 항목 삽입 완료")

if __name__ == "__main__":
    load_housing_info_to_db()
