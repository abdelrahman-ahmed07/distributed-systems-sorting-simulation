import logging
import time

from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

pub = Publisher(client_id="demo-publisher")
pub.connect()
time.sleep(1)

pub.publish(
    topics.INSPECTION_RESULT, messages.INSPECTION_RESULT,
    {"status": "pass", "defect_type": None, "confidence": 0.97},
    product_id="P-1001", source="camera-01",
)
pub.publish(
    topics.SORTER_COMMAND, messages.SORT_COMMAND,
    {"action": "accept", "target_bin": 1},
    product_id="P-1001", source="controller",
)
pub.publish(
    topics.device_status("camera-01"), messages.DEVICE_STATUS,
    {"state": "online"}, source="camera-01",
)
pub.publish(
    topics.SYSTEM_ERROR, messages.SYSTEM_ERROR,
    {"code": "E100", "message": "Test error"}, source="camera-01",
)

time.sleep(1)
pub.close()
print("Done") 