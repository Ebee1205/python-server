# llm_manager.py

from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import time

class LLMManager:
    def __init__(self, ctx):
        self.ctx = ctx
        self.models = ctx.llm_models  # 이미 초기화되어 있다고 가정

    def get(self, key="default"):
        llama = self.models.get(key)
        if not llama:
            self.ctx.log.error(f"[LLM]    !! LLM model '{key}' not found")
        return llama

    def process_prompt(self, key: str, prompt_text: str, is_async: bool = False):
        llama = self.get(key)
        if not llama:
            return "No model"

        prompt = PromptTemplate(input_variables=["input"], template="{input}")
        runnable_chain = prompt | llama

        start = time.time()
        try:
            if is_async:
                return runnable_chain.ainvoke({"input": prompt_text})
            else:
                result = runnable_chain.invoke({"input": prompt_text})
        except Exception as e:
            self.ctx.log.error(f"[LLM]    !! Prompt processing error: {e}")
            return "Prompt failed"

        elapsed = time.time() - start
        output_len = len(result)
        approx_tokens = (len(prompt_text) + output_len) // 4
        tps = approx_tokens / elapsed if elapsed > 0 else 0
        self.ctx.log.debug(f"[LLM]    - Result: {elapsed:.3f}s, tokens≈{approx_tokens}, TPS={tps:.2f}")
        return result

    def destroy(self):
        self.ctx.log.info("[LLM]    - Cleaning up LLM models")
        self.models.clear()
