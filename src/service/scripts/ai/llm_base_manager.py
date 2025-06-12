import time
from abc import ABC, abstractmethod
from langchain.prompts import PromptTemplate

class BaseLLMManager(ABC):
    def __init__(self, ctx):
        self.ctx = ctx
        self.model = None
        self.initialized = False

    def init(self):
        if not self.model:
            self.model = self._get_model()
        if not self.model:
            raise ValueError("[LLM]     !! No LLM model available")
        self.initialized = True
        self.ctx.log.info("[LLM]     - LLMManager initialized")

    def destroy(self):
        self.model = None
        self.initialized = False
        self.ctx.log.info("[LLM]     - LLMManager destroyed")

    def get_chain(self):
        """PromptTemplate과 모델을 조합한 Langchain Runnable 반환"""
        return self._get_prompt_template() | self.model

    # ----------------------------
    # Abstract Methods
    # ----------------------------

    @abstractmethod
    def _get_model(self):
        pass

    @abstractmethod
    def _get_prompt_template(self):
        pass

    @abstractmethod
    def _log_stats(self, prompt_text: str, result: str, start_time: float) -> str:
        pass
