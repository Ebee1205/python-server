# app_context.py
import json

from pydantic import BaseModel
from typing import Any
from typing import Optional

import py_logger
from src.handler.websocket_handler import WebSocketHandler

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
    queue: str
    routing_key: str
    heartbeat: int
    reconnect_delay: int

class HTTPConfig(BaseModel):
    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool

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



class AppContext:
    def __init__(self):
        self.cfg = None

        self.log = None
        
        self.ws_handler = None
        self.db_handler = None
        self.redis_handler = None
        self.rmq_handler = None

    def load_config(self, path: str) -> AppConfig:
        """JSON 파일을 로드하고 AppConfig 모델로 파싱"""
        print("start load config")

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        print("end load config")
        self.cfg = AppConfig(**raw)
    
    def _init_logger(self):
        print("start init logger")

        log_level = self.cfg.logger.level 
        log_path = self.cfg.logger.path
        log_max_files = self.cfg.logger.max_files
        self.log = py_logger.setup_logger(log_level, log_path, log_max_files)

        self.log.debug("end init logger")

    def _init_websocket(self):
        self.log.debug("start init websocket")

        self.ws_handler = WebSocketHandler(self)

    # def _init_mysql(self):

    # def _init_redis(self):

    # def _init_rmq(self):

    def setup_cors(self, app):
        """
        🚧 TEMP: AppContext 내부에서 FastAPI(app)에 CORS 직접 등록

        TODO: 리팩토링 필요. app-level 상태 설정은 middleware 모듈로 이동 권장.
        현재 구조에서는 app_context가 FastAPI 객체에 직접 접근하고 있어     
        책임 분리가 어긋나므로 구조적으로 분리 필요함.
        """

        http_cfg = self.cfg.http_config

        app.add_middleware(
            CORSMiddleware,
            allow_origins=http_cfg.allow_origins,
            allow_credentials=http_cfg.allow_credentials,
            allow_methods=http_cfg.allow_methods,
            allow_headers=http_cfg.allow_headers,
        )

        if self.log:
            self.log.info(f"CORS 설정 완료: {http_cfg.allow_origins}")

    # _destroy() 메서드 추가