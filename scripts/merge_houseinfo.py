import os
import json
from collections import defaultdict

HOUSING_INFO_DIR = "media/announcements/housing_info"
OUTPUT_DIR = "media/announcements/merged_by_name"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def merge_by_house_name():
    for fname in os.listdir(HOUSING_INFO_DIR):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(HOUSING_INFO_DIR, fname), "r", encoding="utf-8") as f:
            data = json.load(f)

        announcement_id = data.get("announcement_id")
        housing_list = data.get("housing_info", [])

        merged = {}

        for h in housing_list:
            house_name = h["name"]

            if house_name not in merged:
                merged[house_name] = {
                    "name": house_name,
                    "address": h.get("address"),
                    "district": h.get("district"),
                    "total_households": h.get("total_households"),
                    "supply_households": [],
                    "type": [],
                    "house_type": [],
                    "elevator": h.get("elevator"),
                    "parking": h.get("parking")
                }

            merged[house_name]["supply_households"].append(h.get("supply_households"))
            merged[house_name]["type"].append(h.get("type"))
            merged[house_name]["house_type"].append(h.get("house_type"))

        merged_list = list(merged.values())

        output = {
            "announcement_id": announcement_id,
            "housing_info": merged_list
        }

        with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ {fname} → {len(merged_list)}개 항목으로 병합 완료")

if __name__ == "__main__":
    merge_by_house_name()
