import json
from typing import Dict, Any

# ✅ run_ai.py의 LLM 관련 함수만 가져옴
from scripts.run_ai import (
    check_priority_with_llm,
    check_eligibility_with_llm,
    qwen_pipe,
)


def analyze_user_eligibility(user_data: Dict[str, Any], announcement_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 데이터와 공고 데이터를 받아
    Qwen 모델을 사용해 자격 및 우선순위를 분석합니다.
    """

    # 1️⃣ Qwen 모델이 준비되었는지 확인
    if qwen_pipe is None:
        raise RuntimeError("Qwen 모델 파이프라인이 초기화되지 않았습니다. run_ai.py에서 모델 로드를 확인하세요.")

    # 2️⃣ 신청자격 판단
    criteria_str = announcement_data.get("application_eligibility", "신청자격 정보 없음")

    try:
        eligibility_result = check_eligibility_with_llm(user_data, criteria_str, {})
    except Exception as e:
        return {
            "is_eligible": False,
            "priority": None,
            "reasons": [f"자격 판단 중 오류 발생: {str(e)}"],
        }

    # 자격 미달 시
    if not eligibility_result.get("is_eligible", False):
        return {
            "is_eligible": False,
            "priority": None,
            "reasons": eligibility_result.get("reasons", ["자격 요건을 충족하지 못했습니다."]),
        }

    # 3️⃣ 자격 충족 시 우선순위 판단
    try:
        priority_result = check_priority_with_llm(user_data, announcement_data)
    except Exception as e:
        priority_result = {"priority": "판단 오류", "reasons": [f"우선순위 판단 중 오류 발생: {str(e)}"]}

    # 4️⃣ 최종 결과 반환
    return {
        "is_eligible": True,
        "priority": priority_result.get("priority", "판단 불가"),
        "reasons": None,
    }


def analyze_user_eligibility_bulk(user_data: Dict[str, Any], announcements: Dict[str, Any]) -> Dict[str, Any]:
    """
    여러 개의 공고(JSON 딕셔너리 묶음)에 대해 일괄 분석 수행
    """
    results = {}

    for filename, announcement_data in announcements.items():
        try:
            results[filename] = analyze_user_eligibility(user_data, announcement_data)
        except Exception as e:
            results[filename] = {
                "is_eligible": False,
                "priority": None,
                "reasons": [f"{filename} 분석 중 오류 발생: {str(e)}"],
            }

    return results
