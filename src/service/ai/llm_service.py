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
    ctx.log.debug("[LLM] Start llm_analyze_dialog")

    combined_text = "\n".join(f"{seg.get('speaker', '화자')} : {seg['text']}" for seg in segments)

    prompt_text = (
        "다음 글을 분석하여 반드시 **한국어로 작성된 JSON 형식**으로 반환하세요.\n\n"
        f"{combined_text}\n\n"
        "결과는 다음 형식을 따라야 하며, 반드시 키/값 모두 한국어여야 합니다:\n"
        "{\n"
        "  \"keyword\": [\"키워드1\", \"키워드2\", \"키워드3\"],\n"
        "  \"mood\": [\"분위기1\", \"분위기2\", \"분위기3\"]\n"
        "}"
    )

    prompt = PromptTemplate(input_variables=["input"], template="{input}")
    runnable_chain = prompt | llama

    result = runnable_chain.invoke({"input": prompt_text})
    ctx.log.debug(f"[LLM] Raw LLM response: {result}")

    parsed = extract_json_from_text(result)
    ctx.log.debug(f"[LLM] Parsed result: {parsed}")
    return parsed
