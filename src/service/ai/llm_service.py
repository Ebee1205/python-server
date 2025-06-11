import re
import json

from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

llama = Ollama(model="llama3.2")  # 필요 시 한국어 모델로 교체

def sanitize_json_string(json_str: str) -> str:
    """
    비표준 JSON 문자열에서 키를 쌍따옴표로 감싸는 등 보정
    예: {keyword: [...]} → {"keyword": [...]}
    """
    return re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_str)

def extract_json_from_text(text: str) -> dict:
    """
    LLM 응답 텍스트에서 JSON 블럭을 추출하고 dict로 파싱
    """
    try:
        match = re.search(r'\{[\s\S]*?\}', text)
        if not match:
            return {"error": "No valid JSON object found", "raw": text}
        
        json_str = sanitize_json_string(match.group(0))
        parsed = json.loads(json_str)
        return parsed
    except Exception as e:
        return {"error": f"JSON parsing failed: {e}", "raw": text}

# LangChain Runnable 방식
async def llm_analyze_dialog(ctx, segments: list[dict]) -> dict:
    """
    사용자 대화 세그먼트를 받아 LLM으로 감성 분석 수행 (한국어 JSON 출력 보장)
    """
    ctx.log.debug("[LLM]    Start llm_analyze_dialog")

    combined_text = "\n".join(f"{seg.get('speaker', '화자')} : {seg['text']}" for seg in segments)

    prompt_text = (
        "다음 글을 분석하여 반드시 **한국어로 작성된 JSON 형식**으로 반환하세요.\n"
        "※ 아래 규칙을 반드시 따르세요:\n"
        "1. JSON 객체는 딱 하나만 있어야 하며, 다른 설명은 없어야 합니다.\n"
        "2. 키는 `keyword` 와 `mood` 로 고정되어야 합니다. 이때 값은 단어로 정의합니다.\n"
        "3. 키와 값 모두 **반드시 한국어**여야 하며, 다른언어가 섞이면 안 됩니다.\n\n"
        f"{combined_text}\n\n"
        "📌 출력 형식 예시 (이 형식과 정확히 동일해야 함):\n"
        "{\n"
        "  \"keyword\": [],\n"
        "  \"mood\": []\n"
        "}"
    )

    prompt = PromptTemplate(input_variables=["input"], template="{input}")
    runnable_chain = prompt | llama

    result = runnable_chain.invoke({"input": prompt_text})
    ctx.log.debug(f"[LLM] Raw LLM response: {result}")

    parsed = extract_json_from_text(result)
    ctx.log.debug(f"[LLM] Parsed result: {parsed}")
    return parsed
