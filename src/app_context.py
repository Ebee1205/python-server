"""
Project: Ankoko-web-server
Author: wavicle (GitHub: @Eunbee1205)
Email: spiverain02@gmail.com
License: All rights reserved. Commercial use requires a license.
@file app_context.py

© 2025 wavicle. All rights reserved.

Unauthorized copying of this file, via any medium, is strictly prohibited.
Proprietary and confidential.
"""

# app_context.py
import json

from pydantic import BaseModel
from typing import Any
from typing import Optional

import py_logger
from src.handler.websocket_handler import WebSocketHandler
from src.handler.redis_handler import RedisHandler
from src.handler.rabbitmq_handler import RabbitMQHandler

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

        self.log.debug("end init websocket")

    def _init_redis(self):
        self.log.debug("start init Redis")

        self.redis_handler = RedisHandler(self)

        self.log.debug("end init Redis")

    def _init_rmq(self):
        self.log.debug("start init RabbitMQ")

        self.rmq_handler = RabbitMQHandler(self)

        self.log.debug("end init RabbitMQ")

    # TODO def _init_mysql(self):
    # TODO _destroy() 메서드 추가