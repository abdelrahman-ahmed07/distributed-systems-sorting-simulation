# MQTT Communication Service

Messaging backbone for the factory production-line project (product inspection and sorting).
Built with Eclipse Mosquitto (Docker) and Python (Paho MQTT 2.x).

## Architecture

```
 Other services (inspection, sorter, dashboard...)
        |  use the Python library, or any MQTT client
        v
 +--------------------------------------------+
 |  mqtt_service (Python, Paho MQTT)          |
 |  config - topics - messages                |
 |  publisher - subscriber (auto-reconnect)   |
 +----------------------+---------------------+
                        | TCP 1883
 +----------------------v---------------------+
 |  Mosquitto broker (Docker container)       |
 +--------------------------------------------+
```

Services never talk to each other directly. A publisher sends a message to a topic and the broker delivers it to every subscriber of that topic.

## Project structure

```
docker-compose.yml          broker definition
mosquitto/config/           mosquitto.conf
src/mqtt_service/           config.py, topics.py, messages.py, publisher.py, subscriber.py
examples/                   demo scripts
tests/                      pytest tests
```

## Installation (Windows 11)

Requirements: Docker Desktop (WSL 2), Python 3.10+, Git.

```powershell
git clone <repo-url>
cd mqtt-communication
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
```

## Running

```powershell
$env:PYTHONPATH = "src"
python examples\run_subscriber.py      # terminal 1
python examples\run_publisher.py       # terminal 2
python examples\run_lastwill_demo.py   # Last Will demo
python -m pytest tests -v              # tests
```

Stop the broker: `docker compose stop`. View logs: `docker compose logs`.

## Configuration

Environment variables (defaults in `src/mqtt_service/config.py`):

| Variable | Default | Meaning |
|---|---|---|
| `MQTT_HOST` | `localhost` | Broker address |
| `MQTT_PORT` | `1883` | Broker port |

To connect from another machine, set `MQTT_HOST` to the IP of the machine running Docker (and allow port 1883 in Windows Firewall).

## Topics

| Purpose | Topic | QoS | Retained |
|---|---|---|---|
| Inspection results | `factory/inspection/result` | 1 | No |
| Sorting commands | `factory/sorter/command` | 1 | No |
| Device status | `factory/device/<device_id>/status` | 1 | Yes |
| System errors | `factory/system/error` | 1 | No |

Subscribe to all device statuses with `factory/device/+/status`.

## JSON message format

Every message uses the same envelope:

```json
{
  "message_id": "bffa3002-6dcb-44c7-afca-087026f5e144",
  "product_id": "P-1001",
  "timestamp": "2026-11-23T01:12:10.823761+00:00",
  "event_type": "inspection_result",
  "data": {"status": "pass", "defect_type": null, "confidence": 0.97},
  "source": "camera-01"
}
```

| Field | Required | Meaning |
|---|---|---|
| `message_id` | yes | Unique UUID. Used to detect duplicates (QoS 1 may deliver twice) and for tracing |
| `product_id` | yes | Product the message is about; `null` if not tied to a product (e.g. device status) |
| `timestamp` | yes | Creation time, UTC, ISO 8601 |
| `event_type` | yes | `inspection_result`, `sort_command`, `device_status`, `system_error` |
| `data` | yes | Payload object, depends on `event_type` |
| `source` | no | Name of the sending service/device |

`data` per event type (**assumed defaults, to be agreed with the team**):

- `inspection_result`: `status` (`pass`/`fail`), `defect_type`, `confidence` (0 to 1)
- `sort_command`: `action` (`accept`/`reject`), `target_bin`
- `device_status`: `state` (`online`/`offline`)
- `system_error`: `code`, `message`

## Reliability

- **QoS 1** (at least once) for results, commands and errors: losing one means a mis-sorted product. Duplicates are possible, so receivers can deduplicate by `message_id`.
- **Retained messages**: the broker stores the last message of a topic and gives it to any new subscriber immediately. Used for device status so late joiners know the current state. Persisted to disk (`persistence true`).
- **Last Will**: a message registered at connect time. If the client dies without a clean disconnect, the broker publishes it. Each device registers `{"state": "offline"}` on its status topic. Note: its `timestamp` is the registration time, not the time of death.
- **Reconnect**: Paho reconnects automatically (delay 1s to 30s). The Subscriber re-subscribes on every connect, because the broker forgets subscriptions after a restart. Malformed messages are logged and skipped.

## Using the library

```python
from mqtt_service import messages, topics
from mqtt_service.publisher import Publisher
from mqtt_service.subscriber import Subscriber

pub = Publisher(client_id="camera-01")
pub.set_last_will("camera-01")
pub.connect()
pub.announce_online("camera-01")
pub.publish(topics.INSPECTION_RESULT, messages.INSPECTION_RESULT,
            {"status": "pass", "defect_type": None, "confidence": 0.97},
            product_id="P-1001", source="camera-01")

def handler(topic, message):
    print(topic, message["data"])

sub = Subscriber(client_id="sorter-01")
sub.subscribe(topics.INSPECTION_RESULT.name, handler)
sub.run_forever()
```

Not using Python? Any MQTT client works: connect to `<broker-ip>:1883` and use the topics and JSON above.

## Manual test scenarios

| # | Scenario | Command | Expected |
|---|---|---|---|
| 1 | Broker up | `docker compose ps` | `Up`, port `1883` |
| 2 | Simple pub/sub | `mosquitto_sub` / `mosquitto_pub` on `test/hello` | `test/hello Hello MQTT` |
| 3 | JSON + multiple topics | run subscriber, then publisher | 4 lines (inspection, sorter, device, error) |
| 4 | Malformed message | publish `garbage` to `factory/inspection/result` | ERROR logged, subscriber keeps running |
| 5 | Retained | `docker exec mosquitto mosquitto_sub -t factory/device/camera-01/status -C 1` | last state immediately |
| 6 | Last Will | `run_lastwill_demo.py` | `online`, then `offline` after about 1.5 x keepalive |
| 7 | Reconnect | `docker compose stop`, wait, `docker compose start` | warning, then reconnect and 4 re-subscriptions |
| 8 | Automated tests | `python -m pytest tests -v` | `10 passed` |

## Security note

The broker is anonymous and unencrypted (development only). For production use `password_file` and TLS (port 8883).
