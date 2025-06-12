# app_context.py
import orjson

from pydantic import BaseModel
from typing import Any
from typing import Optional

import src.modules.py_logger as py_logger
from src.modules.system_monitor import SystemMonitor
from src.handler.websocket_handler import WebSocketHandler
from src.handler.redis_handler import RedisHandler
from src.handler.rabbitmq_handler import RabbitMQHandler
from src.handler.mqtt_handler import MQTTHandler

from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import Ollama

class LoggerConfig(BaseModel):
    level: str
    path: str
    suffix: str
    max_bytes: int
    max_files: str
    rotation: str
    use_console: bool

class MySQLConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db: str

class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: Optional[str] = None

class RMQConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    vhost: str
    exchange: str
    exchange_type: str
    queues: list[dict]
    routing_key: str
    heartbeat: int
    reconnect_delay: int

class MQTTConfig(BaseModel):
    host: str
    port: int
    keepalive: int
    topics: list[str]

class HTTPConfig(BaseModel):
    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool
    
class LLMModelConfig(BaseModel):
    provider: str
    model: str

class LLMConfig(BaseModel):
    models: dict[str, LLMModelConfig]

class AppConfig(BaseModel):
    # 상위 항목 직접 정의
    environment: str
    project_name: str
    api_v1_str: str
    host: str
    port: int
    secret_key: str
    access_token_expire_minutes: int

    # 구성 요소들
    logger: LoggerConfig
    http_config: HTTPConfig
    mysql: MySQLConfig
    redis: RedisConfig
    rmq: RMQConfig
    mqtt: MQTTConfig

    # 시스템 모니터링 관련 기본값 설정
    enable_monitoring: Optional[bool] = True
    monitoring_interval: Optional[int] = 10

    # 서비스 관련
    llm: Optional[LLMConfig] = None


class AppContext:
    def __init__(self):
        self.cfg = {}
        self.log = None
        
        # 핸들러
        self.ws_handler = None
        self.db_handler = None
        self.redis_handler = None
        self.rmq_handler = None
        self.mqtt_handler = None

        # 매니저
        self.system_monitor = None

        # 서비스
        self.llm_models = {}

    def load_config(self, path: str) -> AppConfig:
        """JSON 파일을 로드하고 AppConfig 모델로 파싱"""
        print("+ start load cfg")

        with open(path, "rb") as f:
            raw = orjson.loads(f.read())

        print("- end load cfg")
        self.cfg = AppConfig(**raw)

    def _init_logger(self):
        print("+ start init logger")

        log_level = self.cfg.logger.level 
        log_path = self.cfg.logger.path
        log_max_files = self.cfg.logger.max_files
        self.log = py_logger.setup_logger(log_level, log_path, log_max_files)

        self.log.debug("- end init logger")
        
    def _init_system_manager(self):
        self.log.debug("+ start init system manager")

        if self.cfg.enable_monitoring:
            interval = self.cfg.monitoring_interval
            self.system_monitor = SystemMonitor(self.log, interval)
            self.system_monitor.start()

        self.log.debug("- end init system manager")

    def _init_websocket(self):
        self.log.debug("+ start init websocket")

        self.ws_handler = WebSocketHandler(self)

        self.log.debug("- end init websocket")

    def _init_redis(self):
        self.log.debug("+ start init Redis")

        self.redis_handler = RedisHandler(self)

        self.log.debug("- end init Redis")

    def _init_rmq(self):
        self.log.debug("+ start init RabbitMQ")

        self.rmq_handler = RabbitMQHandler(self)

        self.log.debug("- end init RabbitMQ")

    def _init_mqtt(self):
        self.log.debug("+ start init MQTT")

        self.mqtt_handler = MQTTHandler(self)

        self.log.debug("- end init MQTT")

    def _init_llms(self):
        self.log.debug("+ start init LLMs")

        if self.cfg.llm:
            for key, model_cfg in self.cfg.llm.models.items():
                if model_cfg.provider == "ollama":
                    self.llm_models[key] = Ollama(model=model_cfg.model)
                    self.log.debug(f"[LLM]    - Loaded model '{key}' as '{model_cfg.model}'")
                else:
                    self.log.warning(f"[LLM]    !! Unsupported provider '{model_cfg.provider}' for model '{key}'")
        else:
            self.log.warning("[LLM]    !! No LLM config found")

        self.log.debug("- end init LLMs")

    # TODO def _init_mysql(self):
    # TODO _destroy() 메서드 추가