# scripts/check_ids.py (또는 manage.py shell에서 해도 됨)
from pathlib import Path
import json

base = Path("media/announcements/schedule")
for f in base.glob("*.json"):
    with open(f, encoding="utf-8") as fp:
        data = json.load(fp)
        ann_id = data.get("announcement_id")
        if ann_id is None:
            print(f"❌ {f.name}: ID 없음")
        else:
            print(f"✅ {f.name}: ID = {ann_id}")
