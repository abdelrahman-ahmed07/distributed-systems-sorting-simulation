import json
import uuid
from datetime import datetime, timezone

# أنواع الأحداث
INSPECTION_RESULT = "inspection_result"
SORT_COMMAND = "sort_command"
DEVICE_STATUS = "device_status"
SYSTEM_ERROR = "system_error"

REQUIRED_FIELDS = ("message_id", "product_id", "timestamp", "event_type", "data")


class InvalidMessageError(Exception):
    """الرسالة مش بالشكل المتفق عليه."""


def build_message(event_type, data, product_id=None, source=None):
    """يبني رسالة جديدة بالشكل الموحد ويرجعها كـ dict."""
    message = {
        "message_id": str(uuid.uuid4()),
        "product_id": product_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
    }
    if source is not None:
        message["source"] = source
    return message


def to_json(message):
    """dict -> نص JSON جاهز للإرسال."""
    return json.dumps(message, ensure_ascii=False)


def parse_message(payload):
    """نص JSON (أو bytes) -> dict بعد التحقق من الحقول."""
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    try:
        message = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InvalidMessageError(f"JSON غير صالح: {exc}") from exc

    if not isinstance(message, dict):
        raise InvalidMessageError("الرسالة لازم تكون JSON object")

    missing = [f for f in REQUIRED_FIELDS if f not in message]
    if missing:
        raise InvalidMessageError(f"حقول ناقصة: {missing}")
    if not isinstance(message["data"], dict):
        raise InvalidMessageError("حقل data لازم يكون object")
    return message