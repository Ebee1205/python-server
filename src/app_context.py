# app_context.py
import orjson

from pydantic import BaseModel
from typing import Any
from typing import Optional

import src.modules.py_logger as py_logger
from src.modules.system_monitor import SystemMonitor
from src.handlers.websocket_handler import WebSocketHandler
from src.handlers.redis_handler import RedisHandler
from src.handlers.rabbitmq_handler import RabbitMQHandler
from src.handlers.mqtt_handler import MQTTHandler

from fastapi.middleware.cors import CORSMiddleware

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
        self.llm_manager = {}

    def load_config(self, path: str) -> AppConfig:
        """JSON 파일을 로드하고 AppConfig 모델로 파싱"""
        print("+ start load cfg")

        with open(path, "rb") as f:
            raw = orjson.loads(f.read())

        print("- end load cfg")
        self.cfg = AppConfig(**raw)
        
    def load_json_map(self, name: str, path: str):
        """
        임의의 JSON 파일을 로드하여 ctx에 동적으로 등록
        예: ctx.load_json_map("event_map", "config/event_map.json")
            → self.event_map 로 저장됨
        """
        try:
            with open(path, "rb") as f:
                data = orjson.loads(f.read())

            setattr(self, name, data)
            print(f"> loaded JSON map '{name}' from {path}")
            return True
        except Exception as e:
            print(f"!! failed to load JSON map '{name}' from {path}: {e}")
            return False

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

        self.llm_manager = {}

        if self.cfg.llm:
            from src.service.ai.llm_base_manager import BaseLLMManager, load_all_llm_managers
            load_all_llm_managers()

            for cls in BaseLLMManager.__subclasses__():
                model_key = getattr(cls, "model_key", None)
                manager_key = getattr(cls, "manager_key", None)

                if not model_key or not manager_key:
                    self.log.warning(f"[LLM]     !! {cls.__name__} missing model_key or manager_key")
                    continue

                if model_key not in self.cfg.llm.models:
                    self.log.warning(f"[LLM]     !! No model config found for model_key '{model_key}'")
                    continue

                instance = cls(self)
                try:
                    instance.init()
                    self.llm_manager[manager_key] = instance
                    self.log.debug(f"[LLM]     - Registered LLM manager '{manager_key}' using model '{model_key}' ({cls.__name__})")
                except Exception as e:
                    self.log.error(f"[LLM]     !! Failed to init {cls.__name__}: {e}")
        else:
            self.log.warning("[LLM]     !! No LLM config found")

        self.log.debug("- end init LLMs")


    # TODO def _init_mysql(self):
    # TODO _destroy() 메서드 추가