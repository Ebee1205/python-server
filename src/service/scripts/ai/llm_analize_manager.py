import time
import re
from langchain.prompts import PromptTemplate
from src.service.scripts.ai.llm_base_manager import BaseLLMManager

def sanitize_json_string(json_str: str) -> str:
    """비표준 JSON 문자열에서 키를 쌍따옴표로 감싸는 등 보정"""
    return re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_str)


class AnalizeLLMManager(BaseLLMManager):
    model_key = "default"
    manager_key = "analize"

    def _get_prompt_template(self, task_type: str, content: str) -> str:
        """
        task_type에 따라 다양한 프롬프트 구성.
        모든 출력은 반드시 한국어로 요청.
        """
        if task_type == "analyze":
            return (
                "다음 글을 분석하여 반드시 **한국어로 작성된 JSON 형식**으로 반환하세요.\n"
                "아래 규칙을 반드시 따르세요:\n"
                "1. JSON 객체는 딱 하나만 있어야 하며, 다른 설명은 없어야 합니다.\n"
                "2. 키는 keyword 와 mood 로 고정되어야 하며, 이때 값은 단어로 정의합니다.\n"
                "3. 키와 값 모두 **반드시 한국어**여야 하며, 다른 언어가 섞이면 안 됩니다.\n\n"
                f"{content}\n\n"
                "📌 출력 형식 예시 (이 형식과 정확히 동일해야 함):\n"
                "{\n"
                "  \"keyword\": [],\n"
                "  \"mood\": []\n"
                "}"
            )
        elif task_type == "summarize":
            return (
                "다음 내용을 간결하게 요약해주세요. 반드시 **한국어**로 작성해야 하며, 3문장 이내로 정리하세요.\n\n"
                f"{content}"
            )
        elif task_type == "translate":
            return (
                "다음 문장을 **자연스러운 한국어**로 번역하세요. 설명 없이 번역된 문장만 출력하세요.\n\n"
                f"{content}"
            )
        else:
            raise ValueError(f"[LLM]    !! Unknown task type: {task_type}")

    def _log_stats(self, prompt_text, result, start_time):
        elapsed = time.time() - start_time
        approx_tokens = (len(prompt_text) + len(result)) // 4
        tps = approx_tokens / elapsed if elapsed > 0 else 0
        self.ctx.log.debug(f"[LLM]    - Result: elapsed={elapsed:.3f}s, tokens={approx_tokens}, TPS={tps:.2f}")
        return result

    async def run_task(self, task_type: str, content: str) -> str:
        self.ctx.log.debug(f"[LLM]    - Start run_task (type={task_type})")

        if not self.initialized:
            raise RuntimeError("[LLM]    !! Not initialized")

        prompt_body = self._get_prompt_template(task_type, content)
        prompt = PromptTemplate(input_variables=["input"], template="{input}")
        chain = prompt | self.model

        start = time.time()
        try:
            result = await chain.ainvoke({"input": prompt_body})
        except Exception as e:
            self.ctx.log.error(f"[LLM]    !! Task failed: {e}")
            return f"❌ 오류: {e}"

        result_str = result.strip() if isinstance(result, str) else str(result)
        self._log_stats(prompt_body, result_str, start)
        return result_str
