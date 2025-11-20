import json
import os
import glob
from typing import Dict, Any
from groq import Groq

# --- Groq API 설정 ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"

# 입력 데이터 필드 설명 (프롬프트에 공통 포함)
field_description = '''
[입력 데이터 필드 설명]
- id: 사용자 구별용 id
- age: 나이
- birth_date: 생년월일 (YYYY.MM.DD)
- gender: 성별 (M: 남성, F: 여성)
- is_married: 결혼 여부(true/false)
- residence: 거주지
- university: 대학생 재학중인지 여부 (true/false)
- graduate: 대학 졸업 여부 (true/false)
- employed: 직장 재직중인지 여부 (true/false)
- job_seeker: 취업준비생 여부 (true/false)
- welfare_receipient: 생계, 의료, 주거급여 수급자 가구, 지원대상 한부모 가족, 차상위계층 가구 중 해당사항이 있는지 여부 (true/false)
- parents_own_house: 부모가 주택을 소유하고 있는지 여부 (true: 소유하고 있음(유주택), false: 소유하고 있지 않음(무주택))
- disability_in_family: 자신이나 가구원 중에 본인 명의의 장애인 등록증을 소유하고 있는 사람이 있는지 여부 (true/false)
- subscription_account: 청약 납입 횟수
- total_assets: 총 자산 (원 단위)
- car_value: 소유하고 있는 자동차 가액 (원 단위)
- income_range: 가구당 월평균 소득 구간 (예: "100% 이하", "50% 이히")
- create_at: 계정 생성 날짜 (ISO 8601 형식)
- user: 사용자 구별 id (중복 가능)
- household_members: 가구원 수 (추가된 필드)
'''
# --- 사용자 데이터 ---
TEST_USER_DATA = {
    "age": 23,
    "birth_date": "2002.10.15",
    "gender": "F",
    "is_married": False,
    "residence": "서울시 성북구",
    "university": True,
    "graduate": False,
    "employed": False,
    "job_seeker": True,
    "welfare_receipient": False,
    "parents_own_house": True,
    "disability_in_family": False,
    "subscription_account": 12,
    "total_assets": 10000000,
    "car_value": 0,
    "income_range": "50% 이하",
    "household_members": 1,
}


def extract_json(text: str):
    """응답에서 JSON만 깔끔하게 추출"""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return text[start:end]
    except:
        return text


def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    client = Groq(api_key=GROQ_API_KEY)

    announcement_date = notice_data["application_schedule"].get("announcement_date", "")
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])

    priority_text = "\n".join(
        [f"- {p['priority']}: {', '.join(p['criteria'])}" for p in priority_list]
    ) if priority_list else ""

    prompt = f"""
너는 청약·자격 심사 전문 AI이다.
반드시 **아래 JSON 형식만** 출력해야 한다.

출력 형식:
{{
  "is_eligible": true/false,
  "priority": "",
  "reasons": []
}}

### 공고문 정보
- 모집공고일: {announcement_date}
- 신청자격: {notice_data.get("application_eligibility", "")}
- 순위 기준:
{priority_text}

### 숫자/단위 해석 규칙 (반드시 따를 것)
1. `total_assets`, `car_value`, `subscription_account`, `household_members`, `age` 등은 **정수**로 해석한다.
2. 입력에 쉼표(,)나 '원' 단위가 붙어있어도 숫자만 추출하여 정수로 비교한다.
   - 예: "10,000,000원" -> 10000000
3. `income_range`는 문자열 비교가 아닌 의미 해석으로 처리:
   - "50% 이하"는 가구 소득이 최대 50% 구간임을 뜻함(즉, <=50% 조건).
4. 날짜 비교가 필요하면 YYYY.MM.DD 형식으로 해석하되, 판단 기준이 불분명하면 판단 대신 `reasons`에 "필드 해석 불가: <필드명>"을 추가하라.
5. 숫자 변환에 실패하거나 애매한 표현이 있으면 즉시 `reasons`에 그 원인을 명시하라(예: "필드 해석 불가: total_assets='unknown'").

### 사용자 정보(JSON)
{json.dumps(user_data, ensure_ascii=False)}

### 지시사항 (중요)
1. 출력은 **오직 JSON**만 허용 — 앞뒤 추가 설명 금지.
2. `is_eligible`은 true/false로만 표기.
3. `priority`는 공고의 우선순위 문자열(예: "1순위", "2순위")을 그대로 기입하거나, 해당없음 시 빈 문자열.
4. `reasons`는 부적합 사유 리스트. 적합 시 빈 리스트.
6. null/None 사용 금지.
"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 오직 JSON만 출력하는 엄격한 판정기다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=512
        )

        ai_raw = completion.choices[0].message.content.strip()
        ai_clean = extract_json(ai_raw)
        ai_result = json.loads(ai_clean)

        return {
            "is_eligible": ai_result.get("is_eligible", False),
            "priority": ai_result.get("priority", ""),
            "reasons": ai_result.get("reasons", [])
        }

    except Exception as e:
        return {
            "is_eligible": False,
            "priority": "",
            "reasons": [f"Groq 응답 파싱 오류: {str(e)}"]
        }


# =============================
# 🔥 변경된 부분: 폴더 순회 추가
# =============================

def load_notice_files(folder: str):
    """폴더 내 모든 JSON 파일 경로 불러오기"""
    return glob.glob(os.path.join(folder, "*.json"))


if __name__ == "__main__":
    print("## 🤖 AI 기반 청약 분석(전체 공고) 시작...\n")

    folder_path = "extracted_json"
    notice_files = load_notice_files(folder_path)

    if not notice_files:
        print("⚠ extracted_json 폴더에 JSON 파일이 없습니다.")
        exit()

    for file_path in notice_files:
        print(f"\n📄 공고 분석 중: {os.path.basename(file_path)}")

        # JSON 파일 읽기
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notice_json = json.load(f)
        except Exception as e:
            print(f"[⚠ 파일 오류] {file_path}: {e}")
            continue

        # 기존 함수 그대로 사용
        result = analyze_eligibility_with_ai(TEST_USER_DATA, notice_json)

        print("---")
        print(f"is_eligible: {result['is_eligible']}")
        print(f"priority: \"{result['priority']}\"")
        print("reasons:", result["reasons"])
        print("====================================")
