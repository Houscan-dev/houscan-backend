import os
import json
from collections import Counter, defaultdict

HOUSING_INFO_DIR = "media/announcements/housing_info"

def check_all_ids():
    """모든 JSON 파일의 ID 중복 확인"""
    all_ids = []
    id_to_files = defaultdict(list)  # ID가 어느 파일에서 나왔는지 추적
    
    print("=== ID 중복 확인 ===\n")
    
    json_files = [f for f in os.listdir(HOUSING_INFO_DIR) if f.endswith(".json")]
    
    for fname in sorted(json_files):
        path = os.path.join(HOUSING_INFO_DIR, fname)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ {fname}: JSON 파일 읽기 오류")
            continue
        
        housing_list = data.get("housing_info", [])
        file_ids = []
        
        for i, house in enumerate(housing_list):
            if "id" in house:
                house_id = house["id"]
                all_ids.append(house_id)
                file_ids.append(house_id)
                id_to_files[house_id].append(f"{fname}[{i}]")
        
        print(f"📁 {fname}: {len(file_ids)}개 항목")
        if file_ids:
            print(f"   ID 범위: {min(file_ids)} ~ {max(file_ids)}")
    
    print(f"\n📊 전체 통계:")
    print(f"   총 항목 수: {len(all_ids)}개")
    print(f"   고유 ID 수: {len(set(all_ids))}개")
    
    # 중복 확인
    id_counts = Counter(all_ids)
    duplicates = {id_val: count for id_val, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n❌ 중복 ID 발견: {len(duplicates)}개")
        for id_val, count in sorted(duplicates.items()):
            print(f"   ID {id_val}: {count}번 중복")
            for location in id_to_files[id_val]:
                print(f"     - {location}")
        return False
    else:
        print(f"\n✅ 모든 ID가 고유함!")
        return True

def check_sequential_ids():
    """ID가 연속적인지 확인"""
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
    
    if not all_ids:
        print("❌ ID가 없습니다.")
        return
    
    sorted_ids = sorted(all_ids)
    print(f"\n🔢 ID 연속성 확인:")
    print(f"   최소 ID: {sorted_ids[0]}")
    print(f"   최대 ID: {sorted_ids[-1]}")
    print(f"   예상 개수: {sorted_ids[-1] - sorted_ids[0] + 1}")
    print(f"   실제 개수: {len(sorted_ids)}")
    
    # 빠진 ID 찾기
    expected_ids = set(range(sorted_ids[0], sorted_ids[-1] + 1))
    actual_ids = set(sorted_ids)
    missing_ids = expected_ids - actual_ids
    
    if missing_ids:
        print(f"   ❌ 빠진 ID: {sorted(missing_ids)}")
    else:
        print(f"   ✅ 모든 ID가 연속적입니다!")

def quick_duplicate_check():
    """빠른 중복 확인 (간단한 명령어용)"""
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
    
    unique_count = len(set(all_ids))
    total_count = len(all_ids)
    
    if unique_count == total_count:
        print(f"✅ 중복 없음: {total_count}개 모두 고유")
        return True
    else:
        print(f"❌ 중복 발견: 전체 {total_count}개 중 고유 {unique_count}개")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # 빠른 확인: python script.py quick
        quick_duplicate_check()
    else:
        # 상세 확인
        check_all_ids()
        check_sequential_ids()