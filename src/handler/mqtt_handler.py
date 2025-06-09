# handler/mqtt_handler.py

import paho.mqtt.client as mqtt
import orjson

class MQTTHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cfg = ctx.cfg.mqtt
        self.log = ctx.log
        self.client = mqtt.Client()

        # 콜백 함수 등록
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def connect(self):
        """MQTT 브로커에 연결"""
        try:
            self.log.info("[MQTT]     - Connecting to broker")
            self.client.connect(
                host=self.cfg.host,
                port=self.cfg.port,
                keepalive=self.cfg.keepalive
            )
            self.log.info(f"[MQTT]     - Connected to {self.cfg.host}:{self.cfg.port}")
            self.client.loop_start()
        except Exception as e:
            self.log.error(f"[MQTT]     !! Connection failed: {e}")

    def disconnect(self):
        """MQTT 연결 종료"""
        self.client.loop_stop()
        self.client.disconnect()
        self.log.info("[MQTT]     - Disconnected from broker")

    def subscribe(self, topic):
        """토픽 구독"""
        self.client.subscribe(topic)
        self.log.debug(f"[MQTT]    ++ Subscribed to topic: {topic}")

    def publish(self, topic, payload: dict):
        """메시지 발행"""
        try:
            message = orjson.dumps(payload)
            self.client.publish(topic, message)
            self.log.debug(f"[MQTT]     << Published to {topic}: {message}")
        except Exception as e:
            self.log.error(f"[MQTT]     !! Publish failed to {topic}: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info("[MQTT]     - Connection successful (on_connect)")
        else:
            self.log.warning(f"[MQTT]     !! Connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.log.debug(f"[MQTT]     - Disconnected (code={rc})")

    def on_message(self, client, userdata, msg):
        try:
            payload = orjson.loads(msg.payload)
            self.log.debug(f"[MQTT]     >> Received message from {msg.topic}: {payload}")
            # 메시지 처리 로직 삽입 가능
        except Exception as e:
            self.log.error(f"[MQTT]     !! Message parse error: {e}")
