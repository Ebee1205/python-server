import asyncio
import orjson
from typing import Dict, Optional
import uuid

class RedisStreamHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.stream_name = stream_name
        self.result_stream = result_stream
        self.group = group
        self.consumer_name = f"{ctx.cfg.service_name}-{uuid.uuid4()}"
        self.batch_size = batch_size
        self.block_ms = block_ms
        self.message_router = None
        self.running = False

    async def start(self, router):
        """Start consuming with given message router"""
        self.message_router = router
        self.redis = self.ctx.redis_handler.get_client()
        self.running = True
        
        await self._ensure_group()
        asyncio.create_task(self._consume_loop())

    async def _handle_message(self, stream: str, message_id: str, message: Dict):
        try:
            result = await self.message_router.dispatch(message)
            
            if result and self.result_stream:
                await self.redis.xadd(self.result_stream, {
                    "message_id": message_id,
                    "result": orjson.dumps(result).decode()
                })
                
            await self.redis.xack(stream, self.group, message_id)
            
        except Exception as e:
            self.ctx.log.error(f"[REDIS] Message processing error: {e}")