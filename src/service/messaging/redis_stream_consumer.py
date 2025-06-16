from src.utils.event_dispatcher_utils import dispatch_event
from redis.exceptions import ResponseError
import asyncio

class RedisStreamConsumer:
    def __init__(self, ctx):
        self.ctx = ctx
        cfg = ctx.cfg.redis_consumer
        self.stream_key = cfg.stream_key           # 예: "ankoko:task:stream"
        self.group_name = cfg.group_name           # 예: "worker-group"
        self.consumer_name = cfg.consumer_name     # 예: "consumer-1"

    async def init_group(self):
        try:
            await self.ctx.redis_handler.client.xgroup_create(
                name=self.stream_key, groupname=self.group_name, id="0", mkstream=True
            )
            self.ctx.log.info(f"[REDIS]    - Consumer group '{self.group_name}' created on stream '{self.stream_key}'")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                self.ctx.log.info(f"[REDIS]    - Consumer group '{self.group_name}' already exists")
            else:
                self.ctx.log.error(f"[REDIS]    !! Failed to create group '{self.group_name}': {e}")
                raise

    async def consume(self):
        self.ctx.log.info(
            f"[REDIS]    >> Starting Redis stream consumer: group={self.group_name} "
            f"on stream '{self.stream_key}', consumer={self.consumer_name}"
        )
        while True:
            try:
                resp = await self.ctx.redis_handler.client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_key: '>'},
                    count=1,
                    block=1000
                )

                if not resp:
                    continue

                for stream, messages in resp:
                    self.ctx.log.debug(f"[REDIS]    == Received {len(messages)} message(s) from stream '{stream}'")
                    for msg_id, fields in messages:
                        self.ctx.log.debug(f"[REDIS]    -- Handling message ID {msg_id} | fields={fields}")
                        # 메시지 처리를 비동기 태스크로 분리
                        asyncio.create_task(self._process_message(msg_id, fields))
            except Exception as e:
                self.ctx.log.error(f"[REDIS]    !! Error while consuming stream: {e}")

    # 비동기 처리 분리 함수
    async def _process_message(self, msg_id, fields):
        try:
            await self.handle_message(fields)
            await self.ctx.redis_handler.client.xack(self.stream_key, self.group_name, msg_id)
            self.ctx.log.debug(f"[REDIS]    -- Acknowledged message ID {msg_id}")
        except Exception as e:
            self.ctx.log.error(f"[REDIS]    !! Failed to process message {msg_id}: {e}")


    async def handle_message(self, fields: dict):
        event = fields.get("event")
        if not event:
            self.ctx.log.warning("[REDIS]    -- No 'event' field found in message, skipping")
            return
        self.ctx.log.info(f"[REDIS]    >> Dispatching event '{event}' with fields: {fields}")
        await dispatch_event(ctx=self.ctx, event=event, source_type="redis", msg=fields)
