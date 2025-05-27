import os
import json

HOUSING_INFO_DIR = "media/announcements/housing_info"

def add_ids_to_housing_info():
    for fname in os.listdir(HOUSING_INFO_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(HOUSING_INFO_DIR, fname)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        housing_list = data.get("housing_info", [])
        for idx, h in enumerate(housing_list, start=1):
            h["id"] = idx

        # 덮어쓰기 저장
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ {fname} 처리 완료 ({len(housing_list)}개 항목에 ID 부여)")

if __name__ == "__main__":
    add_ids_to_housing_info()
