import time
from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher

pub = Publisher(client_id="test-camera")
pub.connect()

tests = [
    ("P-2001", {"status": "pass", "defect_type": None, "confidence": 0.97}),
    ("P-2002", {"status": "fail", "defect_type": "scratch", "confidence": 0.95}),
    ("P-2003", {"status": "pass", "defect_type": None, "confidence": 0.60}),
]

for pid, data in tests:
    pub.publish(topics.INSPECTION_RESULT, messages.INSPECTION_RESULT,
                data, product_id=pid, source="test-camera")

time.sleep(1)
print("Done")