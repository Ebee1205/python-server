import time
from langchain.prompts import PromptTemplate
from llm_base_manager import BaseLLMManager

class DefaultLLMManager(BaseLLMManager):
    def _get_model(self):
        return self.ctx.llm_models.get("default")

    def _get_prompt_template(self):
        return PromptTemplate(
            input_variables=["input"],
            template="You are a helpful assistant.\n\n{input}"
        )

    async def process(self, input_text: str) -> str:
        if not self.initialized:
            raise RuntimeError("[LLM]     !! Not initialized")

        chain = self.get_chain()
        start = time.time()

        try:
            result = await chain.ainvoke({"input": input_text})
            return self._log_stats(input_text, result, start)
        except Exception as e:
            self.ctx.log.error(f"[LLM]     !! Processing failed: {e}")
            return "Prompt failed"

    def _log_stats(self, prompt_text, result, start_time):
        elapsed = time.time() - start_time
        approx_tokens = (len(prompt_text) + len(result)) // 4
        tps = approx_tokens / elapsed if elapsed > 0 else 0
        self.ctx.log.debug(
            f"[LLM]     - Elapsed: {elapsed:.3f}s, tokens: {approx_tokens}, TPS: {tps:.2f}"
        )
        return result


# 사용예시
# llm = DefaultLLMManager(ctx)
# llm.init()

# result = await llm.process("What is the capital of France?")
