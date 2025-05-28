import json
import os
from collections import defaultdict

def merge_housing_data():
    """
    같은 이름과 주소를 가진 집들을 하나의 객체로 합치고 
    supply_households, type, house_type을 배열로 묶는 함수
    """
    
    # 폴더 경로 설정
    folder_path = "media/announcements/housing_info/"
    
    # 처리 결과를 저장할 리스트
    processed_files = []
    
    # JSON 파일들 읽기
    try:
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        print(f"발견된 JSON 파일들: {len(json_files)}개")
        
        for filename in json_files:
            file_path = os.path.join(folder_path, filename)
            print(f"처리 중: {filename}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = json.load(file)
                    
                    # housing_info 배열이 있는지 확인
                    if 'housing_info' in content and isinstance(content['housing_info'], list):
                        housing_data = content['housing_info']
                        
                        # 같은 name과 address를 가진 데이터들을 그룹화
                        grouped_data = defaultdict(list)
                        
                        for item in housing_data:
                            if 'name' in item and 'address' in item:
                                # name과 address를 키로 사용
                                key = (item['name'], item['address'])
                                grouped_data[key].append(item)
                        
                        # 그룹화된 데이터를 합치기
                        merged_housing_data = []
                        
                        for (name, address), items in grouped_data.items():
                            if not items:
                                continue
                                
                            # 첫 번째 아이템을 기준으로 시작
                            base_item = items[0].copy()
                            
                            # 배열로 합칠 필드들
                            supply_households = []
                            types = []
                            house_types = []
                            
                            for item in items:
                                # supply_households 수집
                                if 'supply_households' in item and item['supply_households'] is not None:
                                    supply_households.append(item['supply_households'])
                                
                                # type 수집
                                if 'type' in item:
                                    types.append(item['type'])
                                
                                # house_type 수집
                                if 'house_type' in item and item['house_type'] is not None:
                                    house_types.append(item['house_type'])
                            
                            # 중복 제거 (순서 유지)
                            supply_households = list(dict.fromkeys(supply_households)) if supply_households else []
                            types = list(dict.fromkeys(types)) if types else []
                            house_types = list(dict.fromkeys(house_types)) if house_types else []
                            
                            # 배열로 업데이트 (빈 배열이면 원래 값 유지)
                            if len(supply_households) > 1:
                                base_item['supply_households'] = supply_households
                            if len(types) > 1:
                                base_item['type'] = types
                            if len(house_types) > 1:
                                base_item['house_type'] = house_types
                            
                            # id는 첫 번째 항목의 것을 사용
                            merged_housing_data.append(base_item)
                        
                        # 원본 구조 유지하면서 housing_info만 교체
                        processed_content = content.copy()
                        processed_content['housing_info'] = merged_housing_data
                        
                        processed_files.append({
                            'filename': filename,
                            'original_count': len(housing_data),
                            'merged_count': len(merged_housing_data),
                            'content': processed_content
                        })
                        
                        print(f"  - {filename}: {len(housing_data)}개 → {len(merged_housing_data)}개")
                    
                    else:
                        print(f"  - {filename}: housing_info 배열을 찾을 수 없습니다.")
                        
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류 in {filename}: {e}")
            except Exception as e:
                print(f"파일 읽기 오류 in {filename}: {e}")
                
    except FileNotFoundError:
        print(f"폴더를 찾을 수 없습니다: {folder_path}")
        return []
    except Exception as e:
        print(f"폴더 접근 오류: {e}")
        return []
    
    return processed_files

def save_processed_files(processed_files, output_folder="merged_housing_info/"):
    """처리된 파일들을 새 폴더에 저장"""
    try:
        # 출력 폴더 생성
        os.makedirs(output_folder, exist_ok=True)
        
        for file_info in processed_files:
            output_path = os.path.join(output_folder, file_info['filename'])
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(file_info['content'], file, ensure_ascii=False, indent=2)
        
        print(f"\n병합된 파일들이 {output_folder}에 저장되었습니다.")
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")

def print_sample_results(processed_files, sample_count=3):
    """샘플 결과 출력"""
    if not processed_files:
        return
        
    print(f"\n=== 샘플 결과 ===")
    
    # 병합이 실제로 일어난 파일들만 선택
    files_with_merges = [f for f in processed_files if f['original_count'] > f['merged_count']]
    
    if not files_with_merges:
        print("병합된 항목이 없습니다.")
        return
    
    sample_file = files_with_merges[0]
    housing_data = sample_file['content']['housing_info']
    
    print(f"\n파일: {sample_file['filename']}")
    
    # 배열이 포함된 항목들만 표시
    array_items = []
    for item in housing_data:
        if (isinstance(item.get('supply_households'), list) or 
            isinstance(item.get('type'), list) or 
            isinstance(item.get('house_type'), list)):
            array_items.append(item)
    
    for i, item in enumerate(array_items[:sample_count]):
        print(f"\n{i+1}. {item.get('name', 'Unknown')}")
        print(f"   주소: {item.get('address', 'Unknown')}")
        print(f"   공급세대: {item.get('supply_households', [])}")
        print(f"   타입: {item.get('type', [])}")
        print(f"   주택유형: {item.get('house_type', [])}")

def analyze_duplicates(processed_files):
    """중복 분석 결과 출력"""
    print(f"\n=== 중복 분석 결과 ===")
    
    total_original = 0
    total_merged = 0
    files_with_duplicates = 0
    
    for file_info in processed_files:
        total_original += file_info['original_count']
        total_merged += file_info['merged_count']
        
        if file_info['original_count'] > file_info['merged_count']:
            files_with_duplicates += 1
            duplicates_removed = file_info['original_count'] - file_info['merged_count']
            print(f"  {file_info['filename']}: {duplicates_removed}개 중복 제거")
    
    print(f"\n총 {files_with_duplicates}개 파일에서 중복 발견")
    print(f"전체 항목: {total_original}개 → {total_merged}개")
    print(f"총 {total_original - total_merged}개 중복 항목 병합")

if __name__ == "__main__":
    print("=== 주택 정보 병합 스크립트 시작 ===")
    
    # 데이터 병합
    processed_files = merge_housing_data()
    
    if processed_files:
        # 결과 저장
        save_processed_files(processed_files)
        
        # 중복 분석 결과 출력
        analyze_duplicates(processed_files)
        
        # 샘플 결과 출력
        print_sample_results(processed_files)
        
    else:
        print("처리할 데이터가 없습니다.")
    
    print("\n=== 스크립트 완료 ===")