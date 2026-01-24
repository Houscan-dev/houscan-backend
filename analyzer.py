import json
import os
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL_NAME = "gpt-4o"

# --- [1. 수치 계산 및 전처리 함수] ---

def parse_financial_limit_from_criteria(criteria_text: str, keyword: str) -> Optional[int]:
    if keyword not in criteria_text: return None
    start_index = criteria_text.find(keyword)
    search_text = criteria_text[start_index:start_index+100]
    pattern = re.compile(r'([\d,]+\s*억\s*[\d,]*\s*만?\s*원|[\d,]+\s*만\s*원|[\d,]+\s*원)')
    match = pattern.search(search_text)
    if not match: return None
    try:
        cleaned_str = match.group(0).replace(',', '').replace('원', '').replace(' ', '')
        total_amount = 0
        if '억' in cleaned_str:
            parts = cleaned_str.split('억')
            if parts[0].isdigit(): total_amount += int(parts[0]) * 100000000
            if len(parts) > 1 and '만' in parts[1]:
                man_val = parts[1].replace('만', '')
                if man_val.isdigit(): total_amount += int(man_val) * 10000
            elif len(parts) > 1 and parts[1].isdigit():
                total_amount += int(parts[1])
        elif '만' in cleaned_str:
            pure_number = cleaned_str.replace('만', '')
            if pure_number.isdigit(): total_amount = int(pure_number) * 10000
        elif cleaned_str.isdigit(): total_amount = int(cleaned_str)
        return total_amount
    except: return None

def calculate_age(birth_date_str: str, announcement_date_str: str) -> Optional[int]:
    try:
        if len(birth_date_str) == 6:
            current_year = date.today().year
            birth_year_prefix = 19 if int(birth_date_str[:2]) > (current_year % 100) + 1 else 20
            birth_date_str = str(birth_year_prefix) + birth_date_str
        birth_date = datetime.strptime(birth_date_str, "%Y%m%d").date()
        announcement_date = datetime.strptime(announcement_date_str.rstrip('.'), "%Y.%m.%d").date()
        return announcement_date.year - birth_date.year - ((announcement_date.month, announcement_date.day) < (birth_date.month, birth_date.day))
    except: return None

def preprocess_user_data(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    processed_data = {}
    announcement_date_str = notice_data.get("application_schedule", {}).get("announcement_date", "2025.01.01")
    all_text = notice_data.get("application_eligibility", "")
    
    user_age = calculate_age(user_data.get("birth_date", ""), announcement_date_str)
    processed_data["user_age"] = user_age
    NOTICE_AGE_MIN, NOTICE_AGE_MAX = 19, 39 
    processed_data["age_match"] = True if user_age and (NOTICE_AGE_MIN <= user_age <= NOTICE_AGE_MAX) else False

    notice_asset_max = parse_financial_limit_from_criteria(all_text, "자산")
    user_asset = user_data.get("total_assets", 0)
    processed_data["asset_match"] = True if not notice_asset_max or user_asset <= notice_asset_max else False
    
    processed_data["is_home_owner"] = user_data.get("parents_own_house", False)
    income_str = user_data.get("income_range", "100% 이하")
    processed_data["user_income_val"] = int(re.findall(r'\d+', income_str)[0]) if re.findall(r'\d+', income_str) else 100

    return processed_data

# --- [2. 강화된 핵심 분석 엔진] ---

def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    preprocessed = preprocess_user_data(user_data, notice_data)
    
    marriage_map = {"new": "신혼부부(혼인 7년 이내)", "married": "기혼(혼인 7년 초과)", "single": "미혼"}
    
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])
    priority_context = ""
    for p in priority_list:
        priority_context += f"- {p['priority']}: {' / '.join(p['criteria'])}\n"

    user_profile_for_ai = {
        "만_나이": f"{preprocessed['user_age']}세",
        "연령기준_충족여부": "기준 내 포함" if preprocessed['age_match'] else "기준 외(연령 초과 혹은 미달)",
        "자산_상태": "기준 충족" if preprocessed['asset_match'] else "기준액 초과",
        "소득_수준": f"도시근로자 가구당 월평균 소득의 {preprocessed['user_income_val']}%",
        "주택_소유_현황": "유주택자(본인 또는 세대원 집 보유)" if preprocessed["is_home_owner"] else "무주택 세대구성원",
        "현재_혼인_상태": marriage_map.get(user_data.get('is_married'), "미혼"),
        "현재_거주지역": user_data.get('residence'),
        "장애인_가족_여부": "해당됨" if user_data.get('disability_in_family') else "해당 없음"
    }

    final_check_prompt = f"""
    당신은 청약 신청자를 위한 친절한 서비스 상담원입니다. 아래 정보를 바탕으로 적격 여부와 순위를 안내하세요.

    [신청자 프로필]
    {json.dumps(user_profile_for_ai, ensure_ascii=False)}

    [공고문 기본 자격 요건]
    {notice_data.get("application_eligibility", "정보 없음")}

    [순위 결정 기준]
    {priority_context if priority_context else "상세 순위 기준 없음"}

    [안내 문구 작성 지침 - 엄격 준수]
    1. 'reasons' 작성 시 코드상의 변수명(new, true 등)을 절대 노출하지 마세요.
    2. 부적격 사유는 완전한 한국어 문장으로 설명하세요.
    3. 신청자가 탈락한 이유를 공고문의 기준과 대조하여 친절하게 설명하세요.
    4. **매우 중요: 적격(eligible: true)인 경우, 'reasons' 배열은 반드시 빈 배열 []로 출력하세요. 어떠한 텍스트도 넣지 마세요.**
    5. 부적격(eligible: false)인 경우에만 불합격 사유를 'reasons'에 담으세요.
    6. 'priority'는 공고문에 명시된 명칭(1순위, 2순위 등)을 정확히 추출하세요.

    JSON 출력 형식:
    {{ 
      "eligible": bool, 
      "reasons": [], 
      "priority": "문자열" 
    }}
    """
    
    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {"role": "system", "content": "너는 행정 용어를 풀어서 설명하는 상담사이며, 적격자에게는 사유를 적지 않는 규칙을 철저히 지킨다."}, 
            {"role": "user", "content": final_check_prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    ai_res = json.loads(response.choices[0].message.content)

    # 안전장치 로직: AI가 규칙을 어기고 적격자에게 사유를 적었을 경우 Python에서 강제로 비움
    final_eligible = ai_res.get("eligible", False)
    final_reasons = ai_res.get("reasons", [])
    
    if final_eligible:
        final_reasons = [] # 적격이면 사유 리스트 초기화

    return {
        "is_eligible": final_eligible,
        "priority": ai_res.get("priority", "우선순위 해당없음"),
        "reasons": final_reasons,
        "used_criteria": "application_eligibility"
    }

# --- [3. 전체 공고 순회부] ---

def process_all_notices(user_data: Dict[str, Any], all_notices: List[Dict[str, Any]]):
    priority_info = {}
    for notice in all_notices:
        notice_id = str(notice.get("announcement_id") or notice.get("id"))
        result = analyze_eligibility_with_ai(user_data, notice)
        priority_info[notice_id] = result

    return { "success": True, "profile": { **user_data, "priority_info": priority_info } }