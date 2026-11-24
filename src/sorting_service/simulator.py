import logging
import random
import time
from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher
from mqtt_service.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("simulator")

DEVICE_ID = "diverter-01"
MOVE_SECONDS = 1.0     # مدة الحركة
FAILURE_RATE = 0.2     # احتمال العطل (20%)

pub = Publisher(client_id="simulator-pub-01")
pub.set_last_will(DEVICE_ID)


def send_status(op_state, product_id=None, target_bin=None):
    pub.publish(topics.device_status(DEVICE_ID), messages.DEVICE_STATUS,
                {"state": "online", "operation_state": op_state,
                 "target_bin": target_bin},
                product_id=product_id, source=DEVICE_ID)
    log.info("الجهاز: %s (المنتج %s)", op_state, product_id)


def on_command(topic, message):
    try:
        target_bin = message["data"]["target_bin"]
        pid = message["product_id"]
    except KeyError as exc:
        log.error("أمر غلط، حقل ناقص: %s", exc)
        return

    send_status("MOVING", pid, target_bin)
    time.sleep(MOVE_SECONDS)

    if random.random() < FAILURE_RATE:
        send_status("ERROR", pid, target_bin)
    else:
        send_status("DONE", pid, target_bin)

    send_status("IDLE")


if __name__ == "__main__":
    pub.connect()
    send_status("IDLE")
    sub = Subscriber(client_id="simulator-sub-01")
    sub.subscribe(topics.SORTER_COMMAND.name, on_command)
    log.info("الجهاز الوهمي شغال وبيسمع للأوامر...")
    sub.run_forever()