import json
from dotenv import load_dotenv
import os
import glob
from typing import Dict, Any
from groq import Groq

load_dotenv()

# --- Groq API ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = "llama-3.1-8b-instant"

def extract_json(text: str):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return text[start:end]
    except:
        return text

def analyze_eligibility_with_ai(user_data: Dict[str, Any], notice_data: Dict[str, Any]) -> Dict[str, Any]:
    client = Groq(api_key=GROQ_API_KEY)

    # 공고문 날짜
    announcement_date = notice_data.get("application_schedule", {}).get("announcement_date", "")

    # 우선순위 텍스트 정리
    priority_list = notice_data.get("priority_and_bonus", {}).get("priority_criteria", [])
    priority_text = "\n".join(
        [f"- {p.get('priority', '')}: {', '.join(p.get('criteria', []))}" for p in priority_list]
    )

    prompt = f"""
너는 대한민국 청약 자격 검증 및 우선순위 판정 전문가 AI이다.

출력 JSON 구조:
{{
  "is_eligible": true/false,
  "priority": "",  # 예: "1순위", "2순위"
  "reasons": []    # 부적격 사유 또는 판단 불가 사유
}}

### 📌 공고문 정보
- 모집공고일: {announcement_date}
- 신청자격: {notice_data.get("application_eligibility", "")}

### 📌 우선순위 기준
{priority_text}

### 📌 입력 규칙(매우 중요)

1. '청년'은 19 <= age <= 34

2. `income_range`는 다음처럼 의미 기반으로 해석한다:
   - "50% 이하"는 <=50% 조건.
   - "70% 이하"는 <=70% 조건.
   - "100% 이하"는 <=100% 조건.
   - "50% 이하"와 "70% 이하"는 "100% 이하" 조건을 모두 만족.

3. "우선 선발" 조건이 없으면, 서울 거주 여부 기준으로 is_eligible 판단

4. 판단 불가 항목은 반드시 reasons에 기록

5. 출력은 반드시 JSON만. 여분 설명 절대 금지.

6. 'is_eligible'은 '우선 선발'에 해당하지 않으면 false가 아니라 서울에 사는지 여부로 판단한다.

7. '무주택'은 parents_own_house == False

8. 모든 값은 이미 정규화된 상태.

9. reasons에는 모든 부적격 사유 또는 판단 불가 사유를 배열로 담아야 한다.

10. total_assets와 car_value는 이미 원 단위 숫자로 주어지므로 별도 변환 불필요.

### 📌 사용자 정보(JSON)
{json.dumps(user_data, ensure_ascii=False)}
"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 JSON만 출력하는 판정 AI이다."},
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
# 🔹 폴더 내 JSON 읽기
# =============================
def load_notice_files(folder: str):
    return glob.glob(os.path.join(folder, "*.json"))


# =============================
# 🔥 메인 실행
# =============================
if __name__ == "__main__":
    print("## 🤖 AI 기반 청약 분석(전체 공고) 시작...\n")

    folder_path = "extracted_json"
    notice_files = load_notice_files(folder_path)

    if not notice_files:
        print("⚠ extracted_json 폴더에 JSON 파일이 없습니다.")
        exit()

    # 테스트값 그대로 사용
    TEST_USER_DATA = {
        "age": 23,
        "birth_date": "2002-10-15",
        "gender": "F",
        "is_married": False,
        "residence": "서울특별시 성북구",
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

    for file_path in notice_files:
        print(f"\n📄 공고 분석 중: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notice_json = json.load(f)
        except Exception as e:
            print(f"[⚠ 파일 오류] {file_path}: {e}")
            continue

        result = analyze_eligibility_with_ai(TEST_USER_DATA, notice_json)

        print("---")
        print(f"is_eligible: {result['is_eligible']}")
        print(f"priority: \"{result['priority']}\"")
        print("reasons:", result["reasons"])
        print("====================================")
