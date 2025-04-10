# redis_handler.py

import redis
from redis.exceptions import RedisError, ConnectionError


class RedisHandler:
    def __init__(self, ctx):
        self.log = ctx.log
        self.cfg = ctx.cfg.redis
        self.client = None

    def connect(self):
        try:
            if self.client and self.client.ping():
                self.log.info("Redis already connected")
                return

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
                if self.client.ping():
                    self.client.close()
                    self.log.info("Redis connection closed")
                else:
                    self.log.warning("Redis connection already closed or lost")
            except Exception as e:
                self.log.warning(f"Redis disconnect failed: {str(e)}")

    def get_client(self):
        if not self.client:
            raise RuntimeError("Redis client is not connected")
        return self.client
