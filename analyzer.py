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
            birth_year_prefix = 20 if int(birth_date_str[:2]) <= (current_year % 100) else 19
            birth_date_str = str(birth_year_prefix) + birth_date_str
        birth_date = datetime.strptime(birth_date_str, "%Y%m%d").date()
        ann_date = datetime.strptime(announcement_date_str.rstrip('.'), "%Y.%m.%d").date()
        age = ann_date.year - birth_date.year - ((ann_date.month, ann_date.day) < (birth_date.month, birth_date.day))
        return age
    except: return None

def preprocess_user_data(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    processed_data = {}
    announcement_date_str = notice_data.get("application_schedule", {}).get("announcement_date", "2026.01.01")
    all_text = notice_data.get("application_eligibility", "")
    
    user_age = calculate_age(user_data.get("birth_date", ""), announcement_date_str)
    processed_data["user_age"] = user_age
    processed_data["is_underage_at_announcement"] = True if user_age is not None and user_age < 19 else False
    
    notice_asset_max = parse_financial_limit_from_criteria(all_text, "자산")
    user_asset = user_data.get("total_assets", 0)
    processed_data["asset_match"] = True if not notice_asset_max or user_asset <= notice_asset_max else False
    income_str = user_data.get("income_range", "100% 이하")
    processed_data["user_income_val"] = int(re.findall(r'\d+', income_str)[0]) if re.findall(r'\d+', income_str) else 100

    processed_data["is_home_owner"] = user_data.get("parents_own_house", False)
    processed_data["residence"] = user_data.get("residence", "정보 없음")

    # 혼인/수급/장애 여부 명시화
    marriage_val = user_data.get("is_married")
    marriage_map = {"new": "신혼부부(혼인 7년 이내)", "married": "기혼(일반)", "single": "미혼 (싱글)"}
    processed_data["marriage_text"] = marriage_map.get(marriage_val, "미혼 (싱글)")
    processed_data["welfare_text"] = "기초생활수급자/차상위계층 해당" if user_data.get("welfare_receipient") else "해당 없음"
    processed_data["disability_text"] = "장애인 등록 가족 있음" if user_data.get("disability_in_family") else "해당 없음"

    # 학력 및 직업
    status_list = []
    if user_data.get("university"): status_list.append("대학 재학 중")
    if user_data.get("graduate"): status_list.append("대학 졸업(예정)")
    if user_data.get("employed"): status_list.append("현재 직장 취업 중")
    if user_data.get("job_seeker"): status_list.append("취업 준비 중")
    processed_data["job_education_status"] = ", ".join(status_list) if status_list else "정보 없음"
    
    processed_data["subscription_count"] = user_data.get("subscription_account", 0)
    processed_data["ann_date"] = announcement_date_str
    return processed_data

# --- [2. 강화된 핵심 분석 엔진] ---

def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    preprocessed = preprocess_user_data(user_data, notice_data)
    
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])
    priority_context = ""
    for p in priority_list:
        priority_context += f"- {p['priority']}: {' / '.join(p['criteria'])}\n"

    user_profile_for_ai = {
        "공고일": preprocessed["ann_date"],
        "신청자_만_나이(공고일기준)": f"{preprocessed['user_age']}세",
        "연령_미달_여부": "미달(만 19세 미만)" if preprocessed["is_underage_at_announcement"] else "충족(만 19세 이상)",
        "거주지": preprocessed["residence"],
        "주택_소유_현황": "유주택자" if preprocessed["is_home_owner"] else "무주택 세대구성원",
        "현재_혼인_상태": preprocessed["marriage_text"],
        "기초생활수급자_차상위_여부": preprocessed["welfare_text"],
        "장애인_가족_여부": preprocessed["disability_text"],
        "학력_및_직업상태": preprocessed["job_education_status"],
        "청약통장_납입횟수": f"{preprocessed['subscription_count']}회",
        "보유자산_수준": f"도시근로자 소득 {preprocessed['user_income_val']}% 이하"
    }

    final_check_prompt = f"""
    당신은 청약 자격을 심사하는 행정 전문가입니다. 
    [신청자 프로필]을 [공고문 요건]과 대조하여 **논리적 모순 없이** 판단하십시오.

    [신청자 프로필]
    {json.dumps(user_profile_for_ai, ensure_ascii=False)}

    [공고문 기본 자격 요건]
    {notice_data.get("application_eligibility", "정보 없음")}

    [순위 결정 기준]
    {priority_context if priority_context else "상세 순위 기준 없음"}

    [반드시 준수해야 할 논리 심사 규칙]
    1. **혼인 상태 논리 오류 금지 (매우 중요)**:
       - 신청자는 현재 **'{preprocessed['marriage_text']}'** 상태입니다.
       - 만약 신청자가 '미혼 (싱글)'인데, 공고문에 '신혼부부'와 '청년(미혼)' 전형이 모두 있다면, 반드시 '청년(미혼)' 자격 요건을 기준으로 판단하십시오. 
       - 미혼자에게 "신혼부부 요건을 충족하지 않아 부적격" 혹은 "미혼이 아니므로 신청 불가"라는 식의 앞뒤가 맞지 않는 사유를 절대 생성하지 마십시오.
       - "미혼이라서 기혼자 제외 공고에 적합하지 않다"는 식의 잘못된 해석을 하지 마십시오. 미혼을 우대하거나 허용하는 공고라면 적격입니다.

    2. **나이 언급 규칙**:
       - '연령_미달_여부'가 '미달'인 경우에만 공고일 기준 나이를 언급하며 부적격 사유를 작성하십시오.
       - '정상'인 경우, 나이와 관련된 어떠한 칭찬이나 확인 문구(예: "나이는 충족하지만~")도 'reasons'에 넣지 마십시오.

    3. **수급자/장애인 가점**: 
       - 수급자이거나 장애인 가족이 있다면 공고문의 순위나 가점 기준에서 해당 항목을 찾아 반영하십시오.

    [출력 지침]
    1. 'reasons' 배열에는 **오직 탈락의 원인이 되는 미달 요건**만 한국어 문장으로 담으십시오. 충족된 요건은 비우십시오.
    2. 'priority'에는 신청자가 해당하는 실제 순위(예: "1순위")를 적으십시오. 해당 사항이 없으면 반드시 빈 문자열 ""을 출력하십시오.

    JSON 출력 형식:
    {{ "eligible": bool, "reasons": [], "priority": "문자열" }}
    """
    
    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {"role": "system", "content": "너는 행정 서류를 검토하는 냉철한 AI 심사관이다. 신청자의 상태를 공고문과 대조할 때 사실 관계를 오인하지 않으며, 특히 혼인 상태에 따른 전형 구분을 명확히 한다."}, 
            {"role": "user", "content": final_check_prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    ai_res = json.loads(response.choices[0].message.content)

    final_eligible = ai_res.get("eligible", False)
    final_reasons = ai_res.get("reasons", [])
    final_priority = ai_res.get("priority", "")
    
    # 안전장치
    if any(k in str(final_priority).upper() for k in ["N/A", "NONE", "해당 없음", "해당없음"]):
        final_priority = ""

    if final_eligible:
        final_reasons = []

    return {
        "is_eligible": final_eligible,
        "priority": final_priority,
        "reasons": final_reasons,
        "used_criteria": "application_eligibility"
    }

# --- [3. 전체 공고 순회부] ---

def process_all_notices(user_data: Dict[str, Any], all_notices: List[Dict[str, Any]]):
    priority_info = {}
    for notice in all_notices:
        notice_id = str(notice.get("id") or notice.get("announcement_id"))
        result = analyze_eligibility_with_ai(user_data, notice)
        priority_info[notice_id] = result

    return { "success": True, "profile": { **user_data, "priority_info": priority_info } }