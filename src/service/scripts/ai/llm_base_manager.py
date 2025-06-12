import time
from abc import ABC, abstractmethod
from langchain_community.llms import Ollama

class BaseLLMManager(ABC):
    def __init__(self, ctx):
        self.ctx = ctx
        self.model = None
        self.initialized = False

    @property
    def manager_key(self) -> str:
        return self.__class__.manager_key

    @property
    def model_key(self) -> str:
        return self.__class__.model_key

    def init(self):
        if not self.model:
            self.model = self._get_model()
        if not self.model:
            raise ValueError("[LLM]     !! No LLM model available")
        self.initialized = True
        self.ctx.log.info(f"[LLM]     - LLMManager '{self.manager_key}' initialized")

    def destroy(self):
        self.model = None
        self.initialized = False
        self.ctx.log.info(f"[LLM]     - LLMManager '{self.manager_key}' destroyed")

    def get_chain(self):
        """PromptTemplate과 모델을 조합한 Langchain Runnable 반환"""
        return self._get_prompt_template() | self.model

    def _get_model(self):
        model_cfg = self.ctx.cfg.llm.models.get(self.model_key)
        if not model_cfg:
            raise ValueError(f"[LLM]     !! No config found for model_key '{self.model_key}'")

        if model_cfg.provider != "ollama":
            raise ValueError(f"[LLM]     !! Unsupported provider: {model_cfg.provider}")

        return Ollama(model=model_cfg.model)

    # ----------------------------
    # Abstract Methods
    # ----------------------------

    @abstractmethod
    def _get_prompt_template(self):
        pass

    @abstractmethod
    def _log_stats(self, prompt_text: str, result: str, start_time: float) -> str:
        pass
