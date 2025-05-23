# rabbitmq_handler.py

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import AMQPConnectionError
import json

class RabbitMQHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.cfg = ctx.cfg.rmq

        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        try:
            self.log.debug("[RMQ]     - Connecting...")
            self.connection = await aio_pika.connect_robust(
                host=self.cfg.host,
                port=self.cfg.port,
                login=self.cfg.user,
                password=self.cfg.password,
                virtualhost=self.cfg.vhost,
                heartbeat=self.cfg.heartbeat,
                reconnect_interval=self.cfg.reconnect_delay
            )

            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.cfg.exchange,
                ExchangeType(self.cfg.exchange_type),
                durable=True
            )

            self.log.info("[RMQ]     == Connected")

        except AMQPConnectionError as e:
            self.log.error(f"[RMQ]     -- Connection error: {str(e)}")
            raise

    async def disconnect(self):
        if self.connection:
            self.log.debug("[RMQ]     - Disconnecting...")
            await self.connection.close()
            self.log.info("[RMQ]     -- Disconnected")

    def get_exchange(self):
        if not self.exchange:
            self.log.error("[RMQ]     - Exchange not ready")
            raise RuntimeError("Exchange is not initialized")
        return self.exchange

    def get_channel(self):
        if not self.channel:
            self.log.error("[RMQ]     - Channel not ready")
            raise RuntimeError("Channel is not initialized")
        return self.channel

    def get_config(self):
        return self.cfg

    async def consume(self, queue_name: str, router):
        if not self.channel:
            self.log.error("[RMQ]     - Channel not connected")
            raise RuntimeError("Channel is not connected")

        queue = await self.channel.declare_queue(queue_name, durable=True)

        async def _wrapped_callback(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body)
                    await router(self.ctx, data)
                except Exception as e:
                    self.log.error(f"[RMQ]     - Consume error ({queue_name}): {str(e)}")

        await queue.consume(_wrapped_callback)
        self.log.info(f"[RMQ]     == Consuming queue '{queue_name}'")

    async def consume_multi(self, queue_router_pairs: list[tuple[str, callable]]):
        for queue_name, router in queue_router_pairs:
            await self.consume(queue_name, router)
