import logging

from mqtt_service import topics
from mqtt_service.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def on_message(topic, message):
    print(f"[{topic}] {message['event_type']} -> {message['data']}")


sub = Subscriber(client_id="demo-subscriber")
sub.subscribe(topics.INSPECTION_RESULT.name, on_message, qos=1)
sub.subscribe(topics.SORTER_COMMAND.name, on_message, qos=1)
sub.subscribe(topics.SYSTEM_ERROR.name, on_message, qos=1)
sub.subscribe(topics.ALL_DEVICE_STATUS, on_message, qos=1)
sub.run_forever() 