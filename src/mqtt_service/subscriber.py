import logging
import uuid

import paho.mqtt.client as mqtt

from . import config
from .messages import InvalidMessageError, parse_message

log = logging.getLogger("mqtt.subscriber")


class Subscriber:
    def __init__(self, client_id=None, host=None, port=None):
        self.host = host or config.BROKER_HOST
        self.port = port or config.BROKER_PORT
        # client_id ثابت مهم مع clean_session=False عشان البروكر يفتكر الجلسة
        self.client_id = client_id or f"subscriber-{uuid.uuid4().hex[:8]}"
        self._subscriptions = []   # قائمة (topic, qos)
        self._handlers = {}        # topic_filter -> callback

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        # إعادة اتصال تلقائية بتأخير يزيد من 1 لـ 30 ثانية
        self.client.reconnect_delay_set(
            min_delay=config.RECONNECT_MIN_DELAY,
            max_delay=config.RECONNECT_MAX_DELAY,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def subscribe(self, topic, handler, qos=1):
        """سجّل topic و callback. handler(topic, message_dict)"""
        self._subscriptions.append((topic, qos))
        self._handlers[topic] = handler

    # ---- callbacks بتاعة paho ----
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("فشل الاتصال: %s", reason_code)
            return
        log.info("متصل بالبروكر %s:%s", self.host, self.port)
        # نشترك من جديد في كل اتصال (يغطي حالة إعادة الاتصال)
        for topic, qos in self._subscriptions:
            client.subscribe(topic, qos)
            log.info("اشتراك في %s (QoS %s)", topic, qos)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code.value != 0:
            log.warning("انقطع الاتصال (%s)، هحاول أعيد الاتصال...", reason_code)
        else:
            log.info("تم قطع الاتصال")

    def _on_message(self, client, userdata, msg):
        try:
            message = parse_message(msg.payload)
        except InvalidMessageError as exc:
            log.error("رسالة تالفة على %s: %s", msg.topic, exc)
            return  # نتجاهلها ونكمل
        for topic_filter, handler in self._handlers.items():
            if mqtt.topic_matches_sub(topic_filter, msg.topic):
                try:
                    handler(msg.topic, message)
                except Exception:
                    log.exception("خطأ داخل الـ handler")

    # ---- تشغيل ----
    def run_forever(self):
        """يتصل ويفضل شغال. لو البروكر مش موجود يعيد المحاولة."""
        while True:
            try:
                self.client.connect(self.host, self.port, config.KEEPALIVE_SECONDS)
                break
            except OSError as exc:
                log.warning("البروكر مش متاح (%s)، إعادة محاولة بعد 3 ثواني", exc)
                import time
                time.sleep(3)
        self.client.loop_forever(retry_first_connection=True)

    def stop(self):
        self.client.disconnect() 