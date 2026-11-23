import logging
import os
import time

from mqtt_service.publisher import Publisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

pub = Publisher(client_id="camera-01")
pub.set_last_will("camera-01")
pub.connect()
time.sleep(1)
pub.announce_online("camera-01")
time.sleep(1)
print("Online. Killing process abruptly now...")
os._exit(1)