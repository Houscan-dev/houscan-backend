import json
import os
from pathlib import Path

# 1. 모든 JSON 파일 검사
def check_json_files(directory):
    issues = []
    
    for json_file in Path(directory).glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # announcement_id 확인
            if 'announcement_id' not in data:
                issues.append({
                    'file': json_file.name,
                    'issue': 'announcement_id 키 없음',
                    'has_notice_id': 'notice_id' in data
                })
            elif data['announcement_id'] is None:
                issues.append({
                    'file': json_file.name,
                    'issue': 'announcement_id가 null',
                    'value': data.get('announcement_id')
                })
                
        except json.JSONDecodeError as e:
            issues.append({
                'file': json_file.name,
                'issue': f'JSON 파싱 오류: {e}'
            })
    
    return issues

# 2. 일괄 변경 스크립트
def fix_all_json_files(directory):
    fixed_count = 0
    
    for json_file in Path(directory).glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # notice_id가 있으면 announcement_id로 변경
            if 'notice_id' in data and 'announcement_id' not in data:
                data['announcement_id'] = data.pop('notice_id')
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                print(f"✓ 수정: {json_file.name}")
                fixed_count += 1
                
        except Exception as e:
            print(f"✗ 오류 ({json_file.name}): {e}")
    
    print(f"\n총 {fixed_count}개 파일 수정 완료")

# 실행
print("=== JSON 파일 검사 ===")
issues = check_json_files('extracted_json')

if issues:
    print(f"\n문제 있는 파일: {len(issues)}개")
    for issue in issues[:10]:  # 처음 10개만 출력
        print(f"- {issue['file']}: {issue['issue']}")
        if issue.get('has_notice_id'):
            print(f"  → notice_id가 여전히 존재함")
    
    print("\n=== 자동 수정 시작 ===")
    fix_all_json_files('extracted_json')
else:
    print("모든 파일 정상!")