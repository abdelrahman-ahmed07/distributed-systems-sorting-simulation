import logging
from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher
from mqtt_service.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sorter")

CONFIDENCE_THRESHOLD = 0.8
BIN_ACCEPT = 1
BIN_REJECT = 2
BIN_REVIEW = 3

seen_ids = set()


def decide(data):
    status = data["status"]
    confidence = float(data["confidence"])

    if confidence < CONFIDENCE_THRESHOLD:
        return "review", BIN_REVIEW
    if status == "pass":
        return "accept", BIN_ACCEPT
    if status == "fail":
        return "reject", BIN_REJECT
    return "review", BIN_REVIEW


pub = Publisher(client_id="sorter-pub-01")


def on_inspection(topic, message):
    if message["message_id"] in seen_ids:
        log.warning("رسالة مكررة، تم تجاهلها")
        return
    seen_ids.add(message["message_id"])

    try:
        action, target_bin = decide(message["data"])
    except (KeyError, ValueError, TypeError) as exc:
        log.error("بيانات فحص غلط: %s", exc)
        return

    pid = message["product_id"]
    log.info("المنتج %s -> %s (bin %s)", pid, action, target_bin)
    pub.publish(topics.SORTER_COMMAND, messages.SORT_COMMAND,
                {"action": action, "target_bin": target_bin},
                product_id=pid, source="sorter-01")


if __name__ == "__main__":
    pub.connect()
    sub = Subscriber(client_id="sorter-sub-01")
    sub.subscribe(topics.INSPECTION_RESULT.name, on_inspection)
    log.info("خدمة الفرز شغالة وبتسمع...")
    sub.run_forever()