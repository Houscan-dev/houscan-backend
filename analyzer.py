import json
import os
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL_NAME = "gpt-4o-mini"

# --- [수치 계산 및 전처리 함수들은 기존 로직 유지] ---
def parse_financial_limit_from_criteria(criteria_text: str, keyword: str) -> Optional[int]:
    if keyword not in criteria_text: return None
    start_index = criteria_text.find(keyword)
    search_text = criteria_text[start_index:]
    pattern = re.compile(r'([\d,]+\s*억\s*[\d,]*\s*만?\s*원|[\d,]+\s*만\s*원|[\d,]+\s*원)')
    match = pattern.search(search_text)
    if not match: return None
    try:
        cleaned_str = match.group(0).replace(',', '').replace('원', '').replace(' ', '')
        total_amount = 0
        if '억' in cleaned_str:
            parts = cleaned_str.split('억')
            if parts[0].isdigit(): total_amount += int(parts[0]) * 100000000
            if len(parts) > 1 and parts[1]:
                man_parts = parts[1].split('만')
                if man_parts[0].isdigit(): total_amount += int(man_parts[0]) * 10000
                elif parts[1].isdigit(): total_amount += int(parts[1])
        elif '만' in cleaned_str:
            pure_number = cleaned_str.replace('만', '')
            if pure_number.isdigit(): total_amount = int(pure_number) * 10000
        elif cleaned_str.isdigit(): total_amount = int(cleaned_str)
        return total_amount if total_amount > 0 else None
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
    for p in notice_data.get("priority_and_bonus", {}).get("priority_criteria", []):
        all_text += " " + " ".join(p.get("criteria", []))
    
    user_age = calculate_age(user_data.get("birth_date", ""), announcement_date_str)
    NOTICE_AGE_MIN, NOTICE_AGE_MAX = 19, 39
    processed_data["user_age"] = user_age
    processed_data["age_status"] = "🟢 충족" if user_age and (NOTICE_AGE_MIN <= user_age <= NOTICE_AGE_MAX) else "❌ 미충족"

    notice_asset_max = parse_financial_limit_from_criteria(all_text, "자산")
    notice_car_max = parse_financial_limit_from_criteria(all_text, "자동차")
    processed_data["asset_status"] = "🟢 충족" if not notice_asset_max or user_data.get("total_assets", 0) <= notice_asset_max else "❌ 초과"
    processed_data["car_status"] = "🟢 충족" if not notice_car_max or user_data.get("car_value", 0) <= notice_car_max else "❌ 초과"
    return processed_data

# --- [강화된 핵심 분석 엔진] ---

def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    preprocessed_data = preprocess_user_data(user_data, notice_data)
    
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])
    eligibility_text = notice_data.get("application_eligibility", "정보 없음")
    
    user_profile = {
        "현재_만_나이": preprocessed_data["user_age"],
        "거주지": user_data.get('residence'),
        "소득수준": user_data.get('income_range'),
        "취약계층여부": "해당" if user_data.get('welfare_receipient') else "미해당",
        "무주택여부": "무주택" if not user_data.get('parents_own_house') else "유주택",
        "신혼여부": "신혼 아님" if not user_data.get('is_married') else "신혼",
        "대학생여부": "해당" if user_data.get('university') else "미해당",
        "구직자여부": "해당" if user_data.get('job_seeker') else "미해당"
    }

    # 1. 우선순위(priority_criteria) 순차 정밀 탐색
    if priority_list:
        for p_item in priority_list:
            p_name = p_item.get("priority", "순위 미상")
            p_criteria = " ".join(p_item.get("criteria", []))
            
            # [프롬프팅 빡세게 추가]
            check_prompt = f"""
너는 청약 자격 검증 AI이다. 제공된 [사용자 정보]가 [순위 조건]에 부합하는지 논리적으로 판단하라.

### [판단 가이드라인]
1. **소득 논리**: 소득 수준 '50% 이하'는 '100% 이하'에 포함되는 개념이므로, 사용자가 50% 이하를 주장하면 100% 이하 조건은 충족함.
2. **거주지 논리**: '거주지 우선' 조건의 경우, 사용자의 거주지와 조건의 거주지가 자치구 단위까지 일치해야 한다.
3. **무결성**: 제공되지 않은 정보(예: 창업 여부, 부모 소득 등)를 추측하여 판단하지 마라. 오직 주어진 텍스트로만 판단하라.

### [데이터]
- 사용자 정보: {json.dumps(user_profile, ensure_ascii=False)}
- 검증할 순위 조건 ({p_name}): {p_criteria}

반드시 JSON 객체 하나만 출력하라:
{{ "match": bool, "reason": "부합한다면 빈칸, 부합하지 않는다면 사유를 친절한 문장으로" }}
"""
            
            response = client.chat.completions.create(
                model=GPT_MODEL_NAME,
                messages=[{"role": "system", "content": "너는 서론 없이 JSON만 출력하는 청약 자격 판사이다."}, {"role": "user", "content": check_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            match_res = json.loads(response.choices[0].message.content)
            
            if match_res.get("match"):
                return {
                    "is_eligible": True,
                    "priority": p_name,
                    "reasons": [],
                    "used_criteria": "priority_criteria"
                }

    # 2. 우선순위 미달 시 기본자격(application_eligibility) 빡센 검토
    final_check_prompt = f"""
너는 청약 신청자의 기본 자격 적격 여부를 최종 판단하는 AI이다.

### [필수 지침]
1. **나이/자산/차량 가액** 수치는 이미 Python에서 검증되었으므로 LLM은 이에 대해 판단하지 마라.
2. **대상자 정의**: 사용자가 '구직자'이고 공고가 '청년' 대상이라면, 직업 조건보다는 '무주택 세대구성원' 및 '소득' 요건에 집중하라.
3. **환각 방지**: 사용자가 '창업인'이 아니라고 명시되어 있다면, 공고문에 '창업인' 조건이 있더라도 이를 충족한다고 판단하지 마라.
4. **결과 생성**: 부적격인 경우 'reasons'에 **사용자가 충족하지 못한 명확한 사유**만 한국어 문장으로 적어라. 충족한 조건은 적지 마라.

### [데이터]
- 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False)}
- 신청 기본자격: {eligibility_text}

반드시 JSON으로 답하라:
{{ "eligible": bool, "reason": "부적격 사유 문장 (적격 시 빈 문자열)" }}
"""
    
    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[{"role": "system", "content": "너는 신청 자격을 엄격하게 검증하는 전문가이다."}, {"role": "user", "content": final_check_prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    final_res = json.loads(response.choices[0].message.content)

    if final_res['eligible']:
        # Python 수치 검증(나이, 자산) 재확인
        python_fails = []
        if "❌" in preprocessed_data['age_status']: python_fails.append(f"공고일 기준 만나이 {preprocessed_data['user_age']}세로 연령 제한에 해당하지 않습니다.")
        if "❌" in preprocessed_data['asset_status']: python_fails.append("총 자산 보유액이 공고 기준을 초과합니다.")
        if "❌" in preprocessed_data['car_status']: python_fails.append("자동차 가액 기준을 초과하여 신청이 어렵습니다.")
        
        if python_fails:
            return {"is_eligible": False, "priority": "", "reasons": python_fails, "used_criteria": "application_eligibility"}
        
        return {"is_eligible": True, "priority": "우선순위 해당없음", "reasons": [], "used_criteria": "application_eligibility"}
    else:
        return {"is_eligible": False, "priority": "", "reasons": [final_res['reason']], "used_criteria": "application_eligibility"}

# --- [전체 실행부] ---
def process_all_notices(user_data: Dict[str, Any], all_notices: List[Dict[str, Any]]):
    priority_info = {}
    for notice in all_notices:
        notice_id = str(notice.get("id") if notice.get("id") else notice.get("announcement_id"))
        result = analyze_eligibility_with_ai(user_data, notice)
        priority_info[notice_id] = result

    return {
        "success": True,
        "profile": { **user_data, "priority_info": priority_info }
    }