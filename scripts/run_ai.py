import json
import os
import glob
import sys
from typing import Dict, Any, List, Optional
import re 

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
import torch

QWEN_MODEL_ID = "Qwen/Qwen2.5-3B-Instruct" 

# 모델 로드 및 파이프라인 전역 설정 (4-BIT 양자화 강제 적용)
try:
    print(f"[{QWEN_MODEL_ID}] 모델 로드 시작...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    
    # GPU 사용 가능 여부 확인 및 설정
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(QWEN_MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL_ID,
        quantization_config=quantization_config, # 4-bit 설정 적용
        device_map="auto" # GPU VRAM에 모델을 분산 로드하도록 설정
    )

    # 파이프라인 생성
    qwen_pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        # device_map="auto"를 사용했으므로, 파이프라인의 device 인자를 제거
    )

    print(f"[{QWEN_MODEL_ID}] 모델 로드 완료. (사용 장치: {device})")
except Exception as e:
    print(f"[{QWEN_MODEL_ID}] 모델 로드 실패. (필요 패키지 설치 및 GPU 메모리 확인 필요)", file=sys.stderr)
    print(f"오류: {e}", file=sys.stderr)
    qwen_pipe = None 

# JSON 파일 폴더 경로
ANNOUNCEMENT_JSON_DIR = './test2/extracted_json'
# 예시 파일 제외를 위한 리스트 (이전 요구사항 유지)
EXCLUDE_FILENAMES = ['example_announcement_qwen']

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
- income_range: 가구당 월평균 소득 구간 (예: "100% 이하")
- create_at: 계정 생성 날짜 (ISO 8601 형식)
- user: 사용자 구별 id (중복 가능)
'''

# LLM 호출을 대체하는 함수 (JSON 후처리 강화)
def call_qwen_llm(system_content: str, user_content: str) -> str:
    """
    Qwen 파이프라인을 사용하여 LLM을 호출하고 응답을 반환
    """
    if qwen_pipe is None:
        raise RuntimeError("Qwen 모델 파이프라인이 초기화되지 않았습니다. 모델 로드 오류를 확인하세요.")
        
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    
    # 파이프라인으로 텍스트 생성
    try:
        response = qwen_pipe(
            messages,
            do_sample=False,
            max_new_tokens=1024, # 토큰 길이 유지
            temperature=0.0,
        )
        generated_text = response[0]['generated_text']
        
        # Qwen 모델의 응답에서 마지막 메시지의 content만 추출
        if isinstance(generated_text, list) and generated_text:
             text_to_parse = generated_text[-1]['content'] if isinstance(generated_text[-1], dict) and 'content' in generated_text[-1] else str(generated_text)
        else:
             text_to_parse = str(generated_text)
        
        # ✨ 강력한 정규 표현식을 사용하여 JSON 블록만 추출 및 정리 ✨
        # 1. 마크다운 블록 (```json ... ```) 시도
        json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text_to_parse, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 2. 첫 '{'부터 마지막 '}'까지 찾기 시도 (가장 바깥 JSON 객체를 찾음)
            start_index = text_to_parse.find('{')
            end_index = text_to_parse.rfind('}')
            
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_str = text_to_parse[start_index:end_index+1].strip()
            else:
                # JSON을 찾지 못한 경우 전체 텍스트 반환
                return text_to_parse 

        # 3. 최종 문자열 정리: 유니코드 및 제어 문자 제거 (파싱 오류 방지)
        json_str = json_str.strip()
        json_str = re.sub(r'[^\x20-\x7E\t\r\n\xa0\ufeff\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u3000]', '', json_str)
        
        return json_str

    except Exception as e:
        raise RuntimeError(f"Qwen LLM 호출 중 오류 발생: {e}")

# 2. 우선순위 판단 (priority_criteria를 활용)
def check_priority_with_llm(user_data: Dict[str, Any], priority_data: Dict) -> dict:
    """
    LLM을 사용하여 우선순위만 판단
    """
    priority_prompt = f"""
{field_description}

[우선순위 기준]
{json.dumps(priority_data.get("priority_and_bonus", {}).get("priority_criteria", []), ensure_ascii=False, indent=2)}

[사용자 정보]
{json.dumps(user_data, ensure_ascii=False, indent=2)}

위 우선순위 기준에 따라 해당 사용자의 우선순위를 판단해주세요.
- priority_criteria의 각 순위별 criteria 중 하나라도 만족하면 해당 순위로 인정
- 여러 순위에 모두 해당될 경우, priority_criteria 배열에서 더 앞에 있는(더 높은) 순위를 최종 우선순위로 판단
- 어떤 순위에도 해당하지 않으면 "우선순위 해당없음"으로 판단

다음과 같은 JSON 형식으로, 반드시 JSON만 반환하세요. 다른 설명이나 텍스트는 절대 포함하지 마세요:
{{
    "priority": "판단된 우선순위"
}}
"""
    system_content = "당신은 주택 신청 우선순위를 판단하는 전문가입니다. 주어진 우선순위 기준에 따라 정확하게 판단하고, 응답은 반드시 JSON 형식으로만 반환하세요."
    try:
        json_str = call_qwen_llm(system_content, priority_prompt)
        return json.loads(json_str)
    except Exception as e:
        print(f"Qwen 처리 오류 (우선순위): {str(e)}", file=sys.stderr)
        return {
            "priority": "처리 오류",
            "reasons": [f"Qwen 응답 파싱 또는 호출 중 오류 발생: {str(e)}", f"원래 응답 시도: {json_str[:100]}..."]
        }

# 3. 신청자격 판단 (우선순위 결과를 참고정보로 활용)
def check_eligibility_with_llm(user_data: Dict[str, Any], criteria_str: str, priority_result: dict) -> dict:
    """
    LLM을 사용하여 자격만 판단
    """
    # 🌟 추가된 코드: user_assets_str 정의 🌟
    total_assets_value = user_data.get('total_assets', 'N/A')
    user_assets_str = str(total_assets_value)
    if isinstance(total_assets_value, (int, float)):
        # 쉼표를 넣어 포매팅하고 '원'을 붙입니다.
        user_assets_str = f"{total_assets_value:,}원"
    # 🌟 추가된 코드 끝 🌟

    eligibility_prompt = f"""
{field_description}

[신청자격 요건]
{criteria_str}

[사용자 정보]
{json.dumps(user_data, ensure_ascii=False, indent=2)}

[참고 우선순위 정보]
{json.dumps(priority_result, ensure_ascii=False, indent=2)}

**[응답 규칙 - 자격이 없는 경우 (reasons 리스트)]**
1. 문장 끝에는 **마침표(.)**를 사용합니다.
2. **사유는 사용자가 이해할 수 있는 친절하고 자연스러운 한국어 문장으로 작성하며, '필드명: 값'과 같은 개발자 형식이나 영어 표현은 절대 사용하지 않습니다.** (이전 수정 요구사항 반영)
3. **핵심 데이터 절대 준수**: 사용자 정보의 필드 값(True/False 포함)은 사실이며, 이를 부정하는 추론은 절대 허용되지 않습니다. 데이터에 없는 정보**를 기반으로 **시간 경과**나 **미등록 정보** 등을 임의로 **추론**하는 것은 **절대 금지**됩니다. 
4. **허위 정보 및 논리 오류 금지**: 공고문에 명시되지 않은 조건이나, 이미 충족된 조건을 불합격 이유로 들어서는 안 됩니다. 이유를 설명할 때는 **공고문의 해당 요구사항**과 **사용자님의 현재 정보**가 왜 충돌하는지 논리적 근거를 들어 설명해야 합니다.
5. **논리적 OR 조건 오류 금지**: 'A 또는 B' 조건에서 A가 True이면, B가 False인 것을 불합격 사유로 언급해서는 절대 안 됩니다.
6. **결정적인 논리/수치적 근거 명시 및 오류 절대 금지**: 불합격 사유를 제시할 때는 **[신청자격 요건]의 실제 기준(날짜, 금액, 조건)을 먼저 인용하여 언급하고, 사용자 데이터와 비교하여 불합격 이유를 구체적인 수치와 함께 상세하게 서술해야 합니다.** 명백한 날짜/숫자 비교 오류는 절대 용납되지 않으며, 이 경우 가장 큰 감점이 주어집니다. (이전 수정 요구사항 반영)
7. **숫자 데이터 명시**: 사용자님의 총 자산은 **{user_assets_str}**입니다. 공고문에 없는 임의의 자산 기준을 사유로 제시하는 것은 절대 금지됩니다.
8. **허위 정보 및 논리 오류 금지**: 이유를 설명할 때는 **공고문의 해당 요구사항**과 **사용자님의 현재 정보**가 왜 충돌하는지 논리적 근거를 들어 설명해야 합니다.
9. **충족하는 조건에 대해서는 작성하지 마세요.** 충족하지 못한 조건에 대해서만 이유를 설명하세요.
다음과 같은 JSON 형식으로, 반드시 JSON만 반환하세요. 다른 설명이나 텍스트는 절대 포함하지 마세요:
{{
  "is_eligible": true/false,
  "reasons": [
    "자격이 없는 경우: 충족하지 못한 조건1을 자연스러운 글로 풀어서 설명한 문장.",
    "자격이 없는 경우: 충족하지 못한 조건2를 자연스러운 글로 풀어서 설명한 문장.",
    ...
  ]
}}
"""
    system_content = "당신은 주택 신청 자격 판단의 **데이터 기반 논리 전문가**입니다. **[사용자 정보]의 모든 필드 값(True/False 포함)을 엄격히 준수해야 하며, 데이터에 명시적으로 없는 정보를 임의로 추론하여 불합격 사유로 제시하는 것은 절대 금지됩니다.** 'job_seeker: True'라면 취업준비생이 맞고, 'parents_own_house: False'라면 부모가 무주택자입니다. 이 데이터를 기반으로 정확하게 판단하고, 응답은 친절한 한국어 문장으로 작성된 JSON 형식으로만 반환하세요."
    try:
        json_str = call_qwen_llm(system_content, eligibility_prompt)
        return json.loads(json_str)
    except Exception as e:
        print(f"Qwen 처리 오류 (자격): {str(e)}", file=sys.stderr)
        return {
            "is_eligible": False,
            "reasons": [f"Qwen 응답 파싱 또는 호출 중 오류 발생: {str(e)}", f"원래 응답 시도: {json_str[:100]}..."]
        }


# 1. 로컬 폴더에서 공고문 JSON 파일 로드
def load_all_announcement_jsons(json_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    지정된 폴더에서 모든 JSON 파일을 읽어들여 딕셔너리로 반환
    """
    announcements = {}
    print(f"\n[1] 공고 JSON 파일 로드 시작: {json_dir}")
    if not os.path.isdir(json_dir):
        print(f"오류: 폴더 '{json_dir}'가 존재하지 않습니다.")
        return announcements

    for filepath in glob.glob(os.path.join(json_dir, '*.json')):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                announcements[filename] = json.load(f)
            print(f"  - 로드 성공: {filename}")
        except json.JSONDecodeError as e:
            print(f"  - 오류: {filename} 파일 JSON 디코딩 실패: {e}")
        except Exception as e:
            print(f"  - 오류: {filename} 파일 읽기 실패: {e}")

    print(f"[1] 총 {len(announcements)}개의 공고 JSON 파일 로드 완료")
    return announcements


# 테스트용 사용자 데이터 (이전 코드와 동일)
TEST_USER_DATA = {
    "id": 1,
    "age": 23,
    "birth_date": "2003.05.20",
    "gender": "F",
    "is_married": False, # 혼인 여부를 명확히 추가
    "residence": "서울", # 거주지 추가
    "university": True,
    "graduate": False,
    "employed": False,
    "job_seeker": False, # 취업 준비생
    "welfare_receipient": False,
    "parents_own_house": False, # 부모 무주택 가정
    "disability_in_family": False,
    "subscription_account": 0, # 청약 1년 납입
    "total_assets": 1000000,
    "car_value": 0,
    "income_range": "80% 이하", # 월평균소득이 도시근로자 가구당 월평균소득의 80% 이하
    "create_at": "2024-01-01T00:00:00",
    "user": 1
}

# 분석 실행 함수 (이전 코드의 로직 유지)
def analyze_user_eligibility_test(user_data: Dict[str, Any], json_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    테스트용: 사용자 데이터와 로컬 JSON 파일을 기반으로 자격을 분석
    """
    print(f"\n=== analyze_user_eligibility_test 시작 (사용자 ID: {user_data['id']}) ===")
    
    # 1. 모든 공고 JSON 파일 로드
    announcement_jsons = load_all_announcement_jsons(json_dir)
    
    if not announcement_jsons:
        print("분석할 공고 파일이 없습니다.")
        return {}
    
    if qwen_pipe is None:
        print("Qwen 모델이 로드되지 않아 분석을 진행할 수 없습니다.")
        return {"error": "Qwen 모델 로드 실패"}

    # 2. 각 공고에 대해 분석 수행
    print("\n[2] 공고별 분석 시작")
    results = {}
    
    for filename, announcement_data in announcement_jsons.items():
        print(f"\n공고 파일 {filename} 분석 중...")
        
        criteria_str = announcement_data.get("application_eligibility", "신청자격 정보 없음")
        
        # 자격 판단 (우선순위 정보는 자격 판단 후에 얻으므로 초기에는 빈 딕셔너리 전달)
        print(f"파일 {filename}: 자격 판단 시작")
        eligibility_result = check_eligibility_with_llm(user_data, criteria_str, {})
        
        if not eligibility_result.get("is_eligible", False):
            print(f"파일 {filename}: 자격 미달")
            results[filename] = {
                "is_eligible": False,
                "priority": None,
                "reasons": eligibility_result.get("reasons", ["자격 요건을 충족하지 못함"])
            }
            continue

        # 자격 충족 시, 우선순위 판단
        print(f"파일 {filename}: 자격 충족, 우선순위 판단 시작")
        priority_result = check_priority_with_llm(user_data, announcement_data)

        results[filename] = {
            "is_eligible": True,
            "priority": priority_result.get("priority", "판단 불가"),
            "reasons": None
        }
        print(f"파일 {filename}: 분석 완료 (우선순위: {results[filename]['priority']})")
        
    print("\n=== analyze_user_eligibility_test 완료 ===")
    return results

# 테스트 실행
if __name__ == '__main__':
    
    if not os.path.exists(ANNOUNCEMENT_JSON_DIR):
        os.makedirs(ANNOUNCEMENT_JSON_DIR)
        
    example_announcement = {
        "announcement_id": 101,
        "application_eligibility": "만 19세 이상 만 39세 이하의 미혼 청년으로, 무주택세대구성원이며, 해당 세대의 월평균소득이 전년도 도시근로자 가구원수별 가구당 월평균소득의 100% 이하이고, 총 자산이 행복주택 자산기준을 충족해야 합니다.",
        "housing_info": [],
        "residence_period": "최대 10년, 2년 단위로 4회 재계약 가능",
        "priority_and_bonus": {
            "priority_criteria": [
                {
                    "priority": "1순위",
                    "criteria": [
                        "만 19세 이상 만 39세 이하의 청년",
                        "미혼",
                        "무주택세대구성원",
                        "해당 세대의 월평균소득이 전년도 도시근로자 가구원수별 가구당 월평균소득의 100% 이하",
                        "해당 세대의 총 자산이 행복주택 자산기준을 충족"
                    ]
                }
            ],
            "score_items": []
        },
        "application_schedule": {},
        "precautions": ""
    }
    
    example_file_path = os.path.join(ANNOUNCEMENT_JSON_DIR, 'example_announcement_qwen.json')
    with open(example_file_path, 'w', encoding='utf-8') as f:
        json.dump(example_announcement, f, ensure_ascii=False, indent=4)
    print(f"\n테스트를 위해 '{example_file_path}'에 예시 공고 데이터 저장 완료.")
    
    # 분석 실행
    analysis_results = analyze_user_eligibility_test(TEST_USER_DATA, ANNOUNCEMENT_JSON_DIR)
    
    print("\n\n=============== 최종 분석 결과 ===============")
    print(json.dumps(analysis_results, ensure_ascii=False, indent=4))
    print("============================================")