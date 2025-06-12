# src/service/scripts/ai/llm_sandbox_manager.py

import time
from langchain.prompts import PromptTemplate
from .llm_base_manager import BaseLLMManager

class SandboxLLMManager(BaseLLMManager):
    """
    SandboxLLMManager

    - 개발/실험용 LLM 테스트 환경에 사용되는 매니저
    - 자유 입력 프롬프트를 그대로 사용하고, 출력 및 성능 측정에 집중
    """

    manager_key = "sandbox"
    model_key = "default"  # cfg.llm.models["default"] 사용

    def _get_prompt_template(self):
        return PromptTemplate(input_variables=["input"], template="{input}")

    def _log_stats(self, prompt_text: str, result: str, start_time: float) -> str:
        elapsed = time.time() - start_time
        approx_tokens = (len(prompt_text) + len(result)) // 4
        tps = approx_tokens / elapsed if elapsed > 0 else 0

        self.ctx.log.debug(
            f"[LLM]     - Sandbox Result: elapsed={elapsed:.3f}s, tokens={approx_tokens}, TPS={tps:.2f}"
        )
        return result
