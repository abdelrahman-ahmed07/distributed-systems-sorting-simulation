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
MAX_RETRIES = 2

seen_ids = set()
pending = {}


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


def send_command(pid, action, target_bin):
    pub.publish(topics.SORTER_COMMAND, messages.SORT_COMMAND,
                {"action": action, "target_bin": target_bin},
                product_id=pid, source="sorter-01")


def is_duplicate(message):
    mid = message["message_id"]
    if mid in seen_ids:
        return True
    seen_ids.add(mid)
    return False


def on_inspection(topic, message):
    if is_duplicate(message):
        log.warning("رسالة مكررة، تم تجاهلها")
        return

    try:
        action, target_bin = decide(message["data"])
    except (KeyError, ValueError, TypeError) as exc:
        log.error("بيانات فحص غلط: %s", exc)
        return

    pid = message["product_id"]
    pending[pid] = {"action": action, "target_bin": target_bin,
                    "retries": 0, "fallback": False}
    log.info("المنتج %s -> %s (bin %s)", pid, action, target_bin)
    send_command(pid, action, target_bin)


def on_device_status(topic, message):
    if is_duplicate(message):
        return

    pid = message["product_id"]
    state = message["data"].get("operation_state")
    if pid is None or pid not in pending:
        return

    job = pending[pid]

    if state == "DONE":
        log.info("المنتج %s اتفرز بنجاح", pid)
        del pending[pid]

    elif state == "ERROR":
        if job["fallback"]:
            log.error("المنتج %s فشل حتى في review", pid)
            pub.publish(topics.SYSTEM_ERROR, messages.SYSTEM_ERROR,
                        {"code": "E200", "message": "Sorting failed for " + str(pid)},
                        product_id=pid, source="sorter-01")
            del pending[pid]
        elif job["retries"] < MAX_RETRIES:
            job["retries"] += 1
            log.warning("المنتج %s: عطل، إعادة محاولة %s من %s",
                        pid, job["retries"], MAX_RETRIES)
            send_command(pid, job["action"], job["target_bin"])
        else:
            log.warning("المنتج %s: فشلت المحاولات، تحويل لـ review", pid)
            job["action"] = "review"
            job["target_bin"] = BIN_REVIEW
            job["fallback"] = True
            send_command(pid, "review", BIN_REVIEW)


if __name__ == "__main__":
    pub.connect()
    sub = Subscriber(client_id="sorter-sub-01")
    sub.subscribe(topics.INSPECTION_RESULT.name, on_inspection)
    sub.subscribe(topics.ALL_DEVICE_STATUS, on_device_status)
    log.info("خدمة الفرز شغالة وبتسمع...")
    sub.run_forever()