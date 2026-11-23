from dataclasses import dataclass

ROOT = "factory"


@dataclass(frozen=True)
class TopicSpec:
    name: str      # اسم الـ topic
    qos: int       # مستوى الـ QoS
    retain: bool   # هل الرسالة تتخزن في البروكر


# نتائج الفحص
INSPECTION_RESULT = TopicSpec(f"{ROOT}/inspection/result", qos=1, retain=False)

# أوامر الفرز
SORTER_COMMAND = TopicSpec(f"{ROOT}/sorter/command", qos=1, retain=False)

# أخطاء النظام
SYSTEM_ERROR = TopicSpec(f"{ROOT}/system/error", qos=1, retain=False)


def device_status(device_id: str) -> TopicSpec:
    """حالة جهاز معين، مثلاً factory/device/camera-01/status"""
    return TopicSpec(f"{ROOT}/device/{device_id}/status", qos=1, retain=True)


# للاشتراك في حالة كل الأجهزة مرة واحدة (+ تعني أي device_id)
ALL_DEVICE_STATUS = f"{ROOT}/device/+/status"
