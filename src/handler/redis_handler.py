# redis_handler.py

import redis
from redis.exceptions import RedisError, ConnectionError

class RedisHandler:
    def __init__(self, ctx):
        self.log = ctx.log
        self.cfg = ctx.cfg.redis
        self.client = None

    # 원래 목적은 _connect와 분리해서 init() 메서드를 가지고 있으려 했는데 외부 생성 client 주입으로 기능이 약간 바뀜
    def init(self, client: redis.Redis):
        """외부에서 생성한 Redis client를 주입받는 경우"""
        self.client = client
        self.log.debug("Redis client injected externally.")

    def connect(self):
        try:
            self.log.debug("Connecting to Redis...")
            self.client = redis.Redis(
                host=self.cfg.host,
                port=self.cfg.port,
                db=self.cfg.db,
                password=self.cfg.password,
                decode_responses=True
            )

            if self.client.ping():
                self.log.info("Redis connection established")
            else:
                self.log.warning("Redis ping failed")

        except (RedisError, ConnectionError) as e:
            self.log.error(f"Redis connection error: {str(e)}")
            raise

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
                self.log.info("Redis connection closed")
            except Exception as e:
                self.log.warning(f"Redis disconnect failed: {str(e)}")
