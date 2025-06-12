import time
from langchain.prompts import PromptTemplate
from llm_base_manager import BaseLLMManager


def clean_llm_result(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        import re
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned


class OpsLLMManager(BaseLLMManager):
    def _get_model(self):
        model = self.ctx.llm_models.get("default")
        if not model:
            self.ctx.log.error("[LLM]    !! LLM model 'default' not found")
        return model

    def _get_prompt_template(self, function_code: str) -> str:
        return (
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
            f"Convert the following p5.js-based JavaScript code:\n```js\n{function_code}\n```"
        )

    def _log_stats(self, prompt_text, result, start_time):
        elapsed = time.time() - start_time
        approx_tokens = (len(prompt_text) + len(result)) // 4
        tps = approx_tokens / elapsed if elapsed > 0 else 0
        self.ctx.log.debug(
            f"[LLM]    - Result: elapsed={elapsed:.3f}s, approx_tokens={approx_tokens}, TPS={tps:.2f}"
        )
        return result

    async def convert_pattern(self, function_code: str) -> str:
        self.ctx.log.debug("[LLM]    - Start convert_pattern")

        if not self.initialized:
            raise RuntimeError("[LLM]    !! Not initialized")

        prompt_text = self._get_prompt_template(function_code)
        prompt = PromptTemplate(input_variables=["input"], template="{input}")
        chain = prompt | self.model

        start = time.time()
        try:
            result = await chain.ainvoke({"input": prompt_text})
        except Exception as e:
            self.ctx.log.error(f"[LLM]    !! Error during translation: {e}")
            return f"Translation failed: {e}"

        result_str = result.strip()
        self._log_stats(prompt_text, result_str, start)

        cleaned = clean_llm_result(result_str)
        self.ctx.log.debug(f"[LLM]    << Raw LLM response (cleaned):\n{cleaned}")

        return cleaned

# llm = OpsLLMManager(ctx)
# llm.init()

# pattern_result = await llm.convert_pattern(js_function_code)
