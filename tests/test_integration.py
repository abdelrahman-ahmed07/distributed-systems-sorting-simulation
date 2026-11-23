import socket
import threading
import time

import pytest

from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher
from mqtt_service.subscriber import Subscriber


def broker_available():
    try:
        socket.create_connection(("localhost", 1883), timeout=1).close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not broker_available(), reason="broker not running")


def test_publish_and_receive_json():
    received = threading.Event()
    box = {}

    def handler(topic, message):
        box["topic"] = topic
        box["message"] = message
        received.set()

    sub = Subscriber(client_id="pytest-sub")
    sub.subscribe(topics.INSPECTION_RESULT.name, handler)
    sub.client.connect_async(sub.host, sub.port)
    sub.client.loop_start()

    pub = Publisher(client_id="pytest-pub")
    pub.connect()
    time.sleep(1.5)
    pub.publish(topics.INSPECTION_RESULT, messages.INSPECTION_RESULT,
                {"status": "fail", "defect_type": "scratch", "confidence": 0.8},
                product_id="P-TEST")

    assert received.wait(5), "message not received"
    assert box["topic"] == topics.INSPECTION_RESULT.name
    assert box["message"]["product_id"] == "P-TEST"
    assert box["message"]["data"]["defect_type"] == "scratch"

    pub.close()
    sub.client.loop_stop()
    sub.client.disconnect()
    