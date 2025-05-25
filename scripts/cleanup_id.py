import json
with open("media/announcements/announcement_titles_by_id.json", encoding="utf-8") as f:
    raw = json.load(f)

# 새로운 구조로 변환
new = {
    k: {
        "old_title": v,
        "new_title": ""  # 수작업으로 채워넣을 부분
    } for k, v in sorted(raw.items(), key=lambda x: int(x[0]))
}

# 저장
with open("announcement_title_update_map.json", "w", encoding="utf-8") as f:
    json.dump(new, f, ensure_ascii=False, indent=2)
