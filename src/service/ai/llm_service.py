# src/service/ai/llm_service.py
# AI > LLM 관련은 여기서 처리
# TODO I/F 다듬어서 여기에 basic 추가
import re
import random
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

llama = Ollama(model="llama3.2")  # 필요 시 한국어 모델로 교체

def sanitize_json_string(json_str: str) -> str:
    """
    비표준 JSON 문자열에서 키를 쌍따옴표로 감싸는 등 보정
    예: {keyword: [...]} → {"keyword": [...]}
    """
    return re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_str)

import time

async def llm_analyze_dialog(ctx, segments: list[dict]) -> dict:
    """
    사용자 대화 세그먼트를 받아 LLM으로 감성 분석 수행 (한국어 JSON 출력 보장)
    """
    ctx.log.debug("[LLM]    - Start llm_analyze_dialog")

    combined_text = "\n".join(f"{seg.get('speaker', '화자')} : {seg['text']}" for seg in segments)

    prompt_text = (
        "다음 글을 분석하여 반드시 **한국어로 작성된 JSON 형식**으로 반환하세요.\n"
        "아래 규칙을 반드시 따르세요:\n"
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

    start = time.time()
    result = runnable_chain.invoke({"input": prompt_text})
    elapsed = time.time() - start

    # ctx.log.debug(f"[LLM]    << Raw LLM response: {result}")

    parsed = sanitize_json_string(result)
    ctx.log.info(f"[LLM]    << Parsed LLM response: {parsed}")

    # 추정 토큰 수 계산 (대략적인 길이 기준)
    input_len = len(prompt_text)
    output_len = len(result) if isinstance(result, str) else 0
    total_chars = input_len + output_len
    approx_tokens = total_chars // 4  # 한글 기준 토큰 1개 ≈ 4자
    tps = approx_tokens / elapsed if elapsed > 0 else 0

    ctx.log.debug(
        f"[LLM]    - Result: elapsed={elapsed:.3f}s, approx_tokens={approx_tokens}, TPS={tps:.2f}"
    )

    return parsed


# ----------- p5.js 템플릿 변환기
def clean_llm_result(raw: str) -> str:
    cleaned = raw.strip()

    # Remove Markdown code block (```python ... ```)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)

    # Remove list brackets if accidentally wrapped
    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            import ast
            as_list = ast.literal_eval(cleaned)
            if isinstance(as_list, list) and len(as_list) == 1:
                return str(as_list[0])
        except Exception:
            pass  # fallback to original

    return cleaned

async def llm_translate_pattern(ctx, function_code: str) -> str:
    """
    JavaScript pattern draw function 또는 p5.js 코드를 입력받아,
    patterns 리스트에 들어갈 Python 딕셔너리 포맷 문자열로 변환합니다.
    """
    ctx.log.debug("[LLM]     - Start llm_translate_pattern")

    prompt_text = (
        "You are a code converter that extracts visual rendering pattern definitions "
        "from JavaScript functions written for p5.js, and formats them as a single Python dictionary entry for a `patterns` list.\n\n"
        "The input JavaScript code will follow the p5.js structure (e.g., `setup`, `draw`, `createCanvas`, `point`, `noise`, etc).\n\n"
        "Strictly follow these rules:\n"
        "1. The output must be a SINGLE Python dictionary only — do NOT wrap it in a list or array.\n"
        "2. Do NOT include ```python or any markdown-style code block formatting.\n"
        "3. The `name` should be short and descriptive (e.g., 'circleFade').\n"
        "4. The `randomParams` field must contain all `p.xxx` values found in the code, using random functions.\n"
        "5. The `drawColor` is True if the function returns RGB, otherwise False.\n"
        "6. The `code` must contain the original JavaScript code inside triple quotes (`\"\"\"`). Do not modify it.\n"
        "7. Absolutely no explanation, comments, or extra wrapping (such as [ ... ] or 'python'). Just return the dictionary.\n\n"
        f"Convert the following p5.js-based JavaScript code:\n```js\n{function_code}\n```\n"
    )


    prompt = PromptTemplate(input_variables=["input"], template="{input}")
    runnable_chain = prompt | llama

    start = time.time()
    try:
        result = await runnable_chain.ainvoke({"input": prompt_text})
    except Exception as e:
        ctx.log.error(f"[LLM]    !! Error during translation: {e}")
        return f"Translation failed: {e}"

    elapsed = time.time() - start
    result_str = result.strip()
    cleaned = clean_llm_result(result_str)

    ctx.log.debug(f"[LLM]    << Raw LLM response (cleaned):\n{cleaned}")

    # 토큰/성능 로그
    input_len = len(prompt_text)
    output_len = len(result_str)
    approx_tokens = (input_len + output_len) // 4
    tps = approx_tokens / elapsed if elapsed > 0 else 0

    ctx.log.debug(
        f"[LLM]    - Result: elapsed={elapsed:.3f}s, approx_tokens={approx_tokens}, TPS={tps:.2f}"
    )

    return cleaned