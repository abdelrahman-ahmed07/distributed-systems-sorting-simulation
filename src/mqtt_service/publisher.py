import logging
import uuid

import paho.mqtt.client as mqtt

from . import config
from . import topics
from .messages import DEVICE_STATUS, build_message, to_json

log = logging.getLogger("mqtt.publisher")


class Publisher:
    def __init__(self, client_id=None, host=None, port=None):
        self.host = host or config.BROKER_HOST
        self.port = port or config.BROKER_PORT
        self.client_id = client_id or f"publisher-{uuid.uuid4().hex[:8]}"

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        self.client.reconnect_delay_set(
            min_delay=config.RECONNECT_MIN_DELAY,
            max_delay=config.RECONNECT_MAX_DELAY,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Connection failed: %s", reason_code)
        else:
            log.info("Connected to %s:%s", self.host, self.port)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code.value != 0:
            log.warning("Connection lost (%s), reconnecting...", reason_code)
    def set_last_will(self, device_id):
        """لو الاتصال اتقطع فجأة، البروكر ينشر offline نيابة عننا."""
        spec = topics.device_status(device_id)
        will = build_message(DEVICE_STATUS, {"state": "offline"}, source=device_id)
        self.client.will_set(spec.name, to_json(will), qos=spec.qos, retain=True)

    def announce_online(self, device_id):
        """ينشر online على topic حالة الجهاز."""
        spec = topics.device_status(device_id)
        return self.publish(spec, DEVICE_STATUS, {"state": "online"}, source=device_id)

    
    def connect(self):
        self.client.connect_async(self.host, self.port, config.KEEPALIVE_SECONDS)
        self.client.loop_start()

    def publish(self, topic_spec, event_type, data, product_id=None, source=None):
        message = build_message(event_type, data, product_id=product_id, source=source)
        info = self.client.publish(
            topic_spec.name,
            to_json(message),
            qos=topic_spec.qos,
            retain=topic_spec.retain,
        )
        return message, info

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()