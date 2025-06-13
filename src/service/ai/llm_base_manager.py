import time
from abc import ABC, abstractmethod
from langchain_community.llms import Ollama

# TODO system project name에서 받아와 import하는 정보 다르게 해야할듯... 아니다 근데 AI 서버에서 다 불러올거면 상관없을듯도
def load_all_llm_managers():
    from .llm_ops_manager import OpsLLMManager

class BaseLLMManager(ABC):
    """
    BaseLLMManager

    - Ollama 기반 LangChain 모델을 관리하는 추상 부모 클래스입니다.
    - 공통된 초기화 로직, 모델 구성, 체인 생성 메서드를 제공하며,
    자식 클래스에서는 프롬프트 템플릿 구성 및 결과 로그 처리 방식만 구현하면 됩니다.

    필수 속성 (자식 클래스에서 선언해야 함):
    - manager_key: ctx.llm_models[manager_key] 형태로 접근될 고유 식별자
    - model_key: cfg.llm.models[model_key]로 접근하여 사용할 LLM 구성 식별자
    """

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
