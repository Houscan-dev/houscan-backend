import json
from dotenv import load_dotenv
import os
from typing import Dict, Any, List, Optional
from groq import Groq
import re
from datetime import datetime, date
import glob 
import sys # 파일이 없을 경우 종료를 위해 sys 모듈 추가

load_dotenv()

# --- Groq API ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Groq API 키가 없으면 프로그램 종료
if not GROQ_API_KEY:
    print("❌ 오류: GROQ_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해 주세요.")
    sys.exit(1)
    
GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct" 
# --- Groq API ---


def extract_json(text: str):
    """LLM 응답 텍스트에서 JSON 객체만을 추출합니다."""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        raw_json = text[start:end]
        
        # 제어 문자 및 기타 불필요한 문자 제거
        clean_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', raw_json)
        
        return clean_json
    except:
        return text
    
def parse_financial_limit_from_criteria(criteria_text: str, keyword: str) -> Optional[int]:
    """
    기준 텍스트에서 금액을 찾아 정수로 변환합니다. (예: '2억 9900만원' -> 299000000)
    """
    if keyword not in criteria_text:
        return None

    start_index = criteria_text.find(keyword)
    search_text = criteria_text[start_index:]
    
    # [숫자,쉼표] [억] [숫자,쉼표] [만] [원] 형태를 포괄하는 패턴
    pattern = re.compile(r'([\d,]+\s*억\s*[\d,]*\s*만?\s*원|[\d,]+\s*만\s*원|[\d,]+\s*원)')
    
    match = pattern.search(search_text)
    
    if not match:
        return None

    amount_str = match.group(0) 
    
    try:
        # 1. 쉼표(,), 공백, '원' 제거
        cleaned_str = amount_str.replace(',', '').replace('원', '').replace(' ', '')
        
        total_amount = 0
        
        # 2. '억' 단위 처리
        if '억' in cleaned_str:
            parts = cleaned_str.split('억')
            if parts[0].isdigit():
                total_amount += int(parts[0]) * 100000000
            
            if '만' in parts[1]:
                만_parts = parts[1].split('만')
                if 만_parts[0].isdigit():
                    total_amount += int(만_parts[0]) * 10000 
            
            elif parts[1].isdigit():
                 total_amount += int(parts[1])

        # 3. '억'이 없고 '만'만 있는 경우
        elif '만' in cleaned_str:
            pure_number = cleaned_str.replace('만', '')
            if pure_number.isdigit():
                total_amount = int(pure_number) * 10000

        # 4. 단순 숫자만 있는 경우
        elif cleaned_str.isdigit():
             total_amount = int(cleaned_str)
        
        if total_amount > 0:
            return total_amount

    except Exception:
        return None
    
    return None

def calculate_age(birth_date_str: str, announcement_date_str: str) -> Optional[int]:
    """공고일 기준으로 만 나이를 계산합니다. (birth_date: YYMMDD)"""
    try:
        # 1. 생년월일 포맷 처리 (YYMMDD -> YYYYMMDD)
        if len(birth_date_str) == 6:
            current_year = date.today().year
            # 대략적인 세기를 판단 (26년생부터 1900년대로 가정)
            birth_year_prefix = 19 if int(birth_date_str[:2]) > (current_year % 100) + 1 else 20
            birth_date_str = str(birth_year_prefix) + birth_date_str
            
        birth_date = datetime.strptime(birth_date_str, "%Y%m%d").date()
        
        # 2. 공고일 포맷 처리 (YYYY.MM.DD)
        announcement_date_str = announcement_date_str.rstrip('.') 
        announcement_date = datetime.strptime(announcement_date_str, "%Y.%m.%d").date()
        
        # 3. 만 나이 계산 로직
        age = announcement_date.year - birth_date.year - ((announcement_date.month, announcement_date.day) < (birth_date.month, birth_date.day))
        return age
    except Exception:
        return None
    

# --- 2. 프리 프로세싱 함수 (모든 논리 판단 수행) ---
def preprocess_user_data(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 데이터를 공고문 기준과 비교하여 LLM에게 최종 판단 상태를 전달합니다.
    """
    processed_data = {}
    
    # 2.1. 공고문 및 기준 텍스트 준비
    announcement_date_str = notice_data.get("application_schedule", {}).get("announcement_date", "2025.01.01")
    
    # JSON 내 모든 우선순위 텍스트 통합
    all_criteria_text = notice_data.get("application_eligibility", "")
    for p in notice_data.get("priority_and_bonus", {}).get("priority_criteria", []):
         all_criteria_text += " " + " ".join(p.get("criteria", []))
    
    # 2.2. 나이 상태 판단
    user_age = calculate_age(user_data.get("birth_date", ""), announcement_date_str)
    
    # NOTE: 공고문에서 '만19세 이상 ~ 만39세 이하' 기준 추출이 어렵다고 가정하고, 일반적인 청년 기준 하드코딩
    NOTICE_AGE_MIN = 19
    NOTICE_AGE_MAX = 39 
    
    processed_data["user_age"] = user_age
    
    if user_age is None:
        processed_data["age_status"] = "❌ 판단 불가: 생년월일 형식 오류 또는 공고일 미기재"
    elif user_age < NOTICE_AGE_MIN:
        processed_data["age_status"] = f"❌ 나이 기준 미달 (만 {user_age}세 < 만 {NOTICE_AGE_MIN}세)"
    elif user_age > NOTICE_AGE_MAX:
        processed_data["age_status"] = f"❌ 나이 기준 초과 (만 {user_age}세 > 만 {NOTICE_AGE_MAX}세)"
    else:
        processed_data["age_status"] = "🟢 나이 기준 충족" 

    # 2.3. 자산/차량 상태 판단
    
    notice_asset_max = parse_financial_limit_from_criteria(all_criteria_text, "자산")
    notice_car_max = parse_financial_limit_from_criteria(all_criteria_text, "차량")

    user_total_assets = user_data.get("total_assets", 0)
    user_car_value = user_data.get("car_value", 0)

    # 총 자산 상태
    processed_data["asset_status"] = "🟢 자산 기준 충족"
    if notice_asset_max is None:
        processed_data["asset_status"] = "⚠️ 판단 불가: 공고문 기준 자산액 추출 실패"
    elif user_total_assets > notice_asset_max:
        processed_data["asset_status"] = f"❌ 총 자산 기준 초과 ({user_total_assets:,}원 > {notice_asset_max:,}원)"
    else:
        if notice_asset_max is not None:
             processed_data["asset_status"] = f"🟢 자산 기준 충족 ({user_total_assets:,}원 / {notice_asset_max:,}원)"

    # 차량 가액 상태
    processed_data["car_status"] = "🟢 차량 가액 기준 충족"
    if notice_car_max is None:
        processed_data["car_status"] = "⚠️ 판단 불가: 차량 가액 기준액 추출 실패"
    elif user_car_value > notice_car_max:
        processed_data["car_status"] = f"❌ 차량 가액 기준 초과 ({user_car_value:,}원 > {notice_car_max:,}원)"
    else:
        if notice_car_max is not None:
            processed_data["car_status"] = f"🟢 차량 가액 기준 충족 ({user_car_value:,}원 / {notice_car_max:,}원)"
    
    return processed_data

def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    preprocessed_data = preprocess_user_data(user_data, notice_data)
    client = Groq(api_key=GROQ_API_KEY)

    # 우선순위 텍스트 정리
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])
    priority_text = "\n".join(
        [f"- {p.get('priority', '')}: {', '.join(p.get('criteria', []))}" for p in priority_list]
    )
    
    user_income_claim = user_data.get("income_range", "정보 없음") 

    prompt = f"""
너는 청약 자격 검증 AI이다. **모든 판단은 아래 '처리된 사용자 상태'만을 근거로 최종 결론을 도출해야 한다.** 너는 숫자 계산을 할 필요가 없다.

출력 JSON 구조:
{{
  "is_eligible": true/false,
  "priority": "",  # 예: "1순위"
  "reasons": [
        "Python이 판단한 미충족 사유 또는 LLM이 판단한 비수치 미충족 사유를 자연스러운 글로 풀어서 설명한 문장.",
        "두 번째 미충족 사유 (중복 없이).",
        ...
    ]
}}



### 📌 공고문 기준 정보
- 신청자격: {notice_data.get("application_eligibility", "정보 없음")}

### 📌 처리된 사용자 상태 (LLM이 최종 판단할 근거)
- 나이 상태: {preprocessed_data['age_status']}
- 주택 소유 상태: {'무주택' if not user_data.get('parents_own_house', True) else '주택 소유'}
- 자산 상태: {preprocessed_data['asset_status']}
- 차량 가액 상태: {preprocessed_data['car_status']}
- 사용자 소득 범위 주장: {user_income_claim}
- 거주지: {user_data.get("residence", "정보 없음")}

### 📌 우선순위 기준
{priority_text}

### [최고 우선순위 규칙]
1. **Python 실패 수용**: [Python 선행 검증 결과]에 명시된 미충족 사유는 **절대적인 사실**이며, 최종 `reasons` 리스트에 포함되어야 합니다.
2. **LLM의 역할**: [신청자격 요건] 및 [사용자 정보]를 바탕으로, **비수치적 필수 조건** (예: 가구 구성원 수)만 검증하여 미충족 사유를 자연어 문장으로 생성합니다.
3. **ONLY FAILURE & NO BONUS (최대 금지)**: 최종 `reasons`에는 **오직 부적격 사유만** 포함해야 합니다. **충족하는 조건**, **우대 사항**, **판단 불가 관련 내용**, 또는 **검증 후 충족된 내용**은 **절대로 포함하지 마세요.**
4. **출력 문장 품질:** 부적격 사유가 여러 개인 경우, **모든 필수 조건 미달 사유를 하나의 간결하고 포괄적인 문장으로 통합**하여 설명합니다. (예: "만 19세 이상이라는 연령 요건과 무주택 세대구성원 요건을 동시에 충족하지 못했습니다.")
5. **필드/값 언급 금지:** 사용자 데이터 필드명이나 필드값(예: university, job_seeker)을 직접적으로 언급하지 마세요.

### 📌 최종 판단 규칙 (Groq AI 수행)

1. **is_eligible 결정:** '나이 상태', '자산 상태', '차량 가액 상태'의 **상태 텍스트**에 '❌'가 포함되어 있다면 `is_eligible`은 **`false`** 이다. '⚠️'만 있다면 `is_eligible`은 **`true`** 로 하되, 이유(reasons)에 포함한다.
2. **priority 결정:** `is_eligible`이 true일 경우에만, '거주지', '소득 범위 주장', '주택 소유 상태'를 '우선순위 기준'과 **자연어 매칭**하여 가장 높은 순위를 반환한다.
3. **reasons:** 상태 텍스트에 포함된 '❌' 또는 '⚠️' 사유를 모두 기록한다.
**출력은 반드시 JSON만. 여분 설명 절대 금지.**
"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 위에 제공된 정보만을 기반으로, 요청된 JSON 구조와 규칙을 완벽하게 준수하여 판단 결과 JSON만 출력하는 AI이다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=512
        )

        raw = completion.choices[0].message.content.strip()
        clean = extract_json(raw)
        ai_result = json.loads(clean)

        return {
            "is_eligible": ai_result.get("is_eligible", False),
            "priority": ai_result.get("priority", ""),
            "reasons": ai_result.get("reasons", [])
        }

    except Exception as e:
        return {
            "is_eligible": False,
            "priority": "",
            "reasons": [f"AI 응답 파싱 오류: {str(e)}"]
        }

# =============================
# 🔥 테스트 실행 (실제 공고 JSON 파일 순회)
# =============================
if __name__ == "__main__":
    
    # 🧑 사용자 모델 필드와 일치하는 데이터 구성 (단일 사용자)
    TEST_USER_DATA = {
        "birth_date": "040417", 
        "gender": "F",
        "university": True, 
        "graduate": False,
        "employed": True, 
        "job_seeker": False,
        "is_married": True,
        "residence": "도봉구", 
        "welfare_receipient": False,
        "parents_own_house": True, 
        "disability_in_family": False,
        "subscription_account": 12,
        "total_assets": 150000000,
        "car_value": 4000000,      
        "income_range": "50% 이하", 
    }

    # 1. extracted_json 디렉토리에서 모든 JSON 파일 경로를 가져옴
    json_files = glob.glob("./extracted_json/*.json")
    
    if not json_files:
        print("⚠️ 경고: './extracted_json/' 디렉터리에서 JSON 파일을 찾을 수 없습니다. 테스트를 진행할 수 없습니다.")
        sys.exit(0) # 파일이 없으면 정상 종료

    loaded_notices = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notice_data = json.load(f)
                loaded_notices.append((notice_data, os.path.basename(file_path)))
        except Exception as e:
            print(f"❌ 오류: 파일 {file_path} 로드 실패 - {e}")
            
    if not loaded_notices:
        print("⚠️ 경고: 로드에 성공한 공고 파일이 없습니다. 테스트를 진행할 수 없습니다.")
        sys.exit(0)

    # 2. 로드된 각 공고문에 대해 분석 수행
    for notice_data, filename in loaded_notices:
        print("\n" + "="*80)
        print(f"## 📋 공고 분석 시작: {filename} (ID: {notice_data.get('announcement_id', 'N/A')})")
        print("="*80)
        
        # 2.1. 프리 프로세싱 결과 출력
        preprocessed = preprocess_user_data(TEST_USER_DATA, notice_data)
        print("--- 💡 처리된 사용자 상태 (Pre-processing 결과) ---")
        print(json.dumps(preprocessed, ensure_ascii=False, indent=2))
        print("-------------------------------------------------")
        
        # 2.2. AI 분석 결과 출력
        result = analyze_eligibility_with_ai(TEST_USER_DATA, notice_data)

        print("\n--- ✅ 최종 AI 판단 결과 ---")
        print(f"is_eligible: {result['is_eligible']}")
        print(f"priority: \"{result['priority']}\"")
        print("reasons:", result["reasons"])
        print("====================================")