# app_context.py
import json

from pydantic import BaseModel
from typing import Any
from typing import Optional

import py_logger

class LoggingConfig(BaseModel):
    level: str
    path: str
    suffix: str
    max_bytes: int
    max_files: int
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
    logging: LoggingConfig
    mysql: MySQLConfig
    redis: RedisConfig
    rmq: RMQConfig

class AppContext:
    def __init__(self):
        self.cfg = None

        self.log = None
        self.db_handler = None
        self.redis_handler = None
        self.rmq_handler = None

    def load_config(self, path: str) -> AppConfig:
        """JSON 파일을 로드하고 AppConfig 모델로 파싱"""
        print("start load config")

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        print("end load config")
        return AppConfig(**raw)
    
    def _init_logger(self):
        print("start init logger")

        log_level = self.cfg.logging.Level
        log_path = self.cfg.logging.path
        log_max_files = self.cfg.logging.max_files
        self.log = py_logger.setup_logger(log_level, log_path, log_max_files)

        self.log.debug("end init logger")

    # def _init_mysql(self):

    # def _init_redis(self):

    # def _init_rmq(self):
