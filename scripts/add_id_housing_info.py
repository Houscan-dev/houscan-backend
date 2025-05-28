import os
import json
from collections import defaultdict

HOUSING_INFO_DIR = "media/announcements/housing_info"

def add_consistent_ids_to_housing_info():
    """간단하게 ID 부여"""
    
    current_id = 1
    
    for fname in os.listdir(HOUSING_INFO_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(HOUSING_INFO_DIR, fname)
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        housing_list = data.get("housing_info", [])
        
        # 기존 ID 제거하고 새로 부여
        for i, house in enumerate(housing_list):
            house.pop("id", None)  # 기존 ID 제거
            house["id"] = current_id
            current_id += 1
        
        # 파일 저장
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {fname} 처리 완료 ({len(housing_list)}개 항목, ID: {current_id-len(housing_list)} ~ {current_id-1})")



def check_duplicate_ids():
    """중복 ID 확인"""
    all_ids = []
    
    for fname in os.listdir(HOUSING_INFO_DIR):
        if not fname.endswith(".json"):
            continue
            
        path = os.path.join(HOUSING_INFO_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        housing_list = data.get("housing_info", [])
        for house in housing_list:
            if "id" in house:
                all_ids.append(house["id"])
    
    duplicates = []
    seen = set()
    for id_val in all_ids:
        if id_val in seen:
            duplicates.append(id_val)
        seen.add(id_val)
    
    if duplicates:
        print(f"❌ 중복 ID 발견: {set(duplicates)}")
        return False
    else:
        print(f"✅ 모든 ID가 고유함 (총 {len(all_ids)}개)")
        return True

if __name__ == "__main__":
    print("=== 주택정보 ID 부여 스크립트 ===\n")
    
    # 중복 확인
    print("1. 현재 상태 확인:")
    check_duplicate_ids()
    
    print("\n2. ID 재부여:")
    add_consistent_ids_to_housing_info()
    
    print("\n3. 최종 확인:")
    check_duplicate_ids()