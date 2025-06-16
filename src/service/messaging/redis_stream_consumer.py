from src.utils.event_dispatcher_utils import dispatch_event
from redis.exceptions import ResponseError

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
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def consume(self):
        while True:
            resp = await self.ctx.redis_handler.client.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_key: '>'},
                count=1,
                block=1000
            )

            for stream, messages in resp:
                for msg_id, fields in messages:
                    await self.handle_message(fields)
                    await self.ctx.redis_handler.client.xack(self.stream_key, self.group_name, msg_id)

    async def handle_message(self, fields: dict):
        event = fields.get("event")
        if not event:
            self.ctx.log.warning("[REDIS] - No event field found in message")
            return
        await dispatch_event(ctx=self.ctx, event=event, source_type="redis", msg=fields)
