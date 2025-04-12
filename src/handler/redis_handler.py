# redis_handler.py

from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError


class RedisHandler:
    def __init__(self, ctx):
        self.log = ctx.log
        self.cfg = ctx.cfg.redis
        self.client: Redis = None

    async def connect(self):
        try:
            if self.client:
                try:
                    if await self.client.ping():
                        self.log.info("Redis already connected")
                        return
                except Exception:
                    pass  # 연결 끊겼을 수 있음 → 재연결 진행

            self.log.debug("Connecting to Redis...")
            self.client = Redis(
                host=self.cfg.host,
                port=self.cfg.port,
                db=self.cfg.db,
                password=self.cfg.password,
                decode_responses=True
            )

            if await self.client.ping():
                self.log.info("Redis connection established")
            else:
                self.log.warning("Redis ping failed")

        except (RedisError, ConnectionError) as e:
            self.log.error(f"Redis connection error: {str(e)}")
            raise

    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
                self.log.info("Redis connection closed")
            except Exception as e:
                self.log.warning(f"Redis disconnect failed: {str(e)}")

    # 사용할 때 비동기 호출 (await client.get(...))
    def get_client(self) -> Redis:
        if not self.client:
            raise RuntimeError("Redis client is not connected")
        return self.client