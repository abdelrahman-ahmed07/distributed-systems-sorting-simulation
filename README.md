# Sorting Service & Device Simulation (Member 3)

This part of the project decides where each inspected product goes (accept, reject, or review bin) and simulates the physical sorting device. It is built on top of the MQTT communication layer (`src/mqtt_service`) written by Member 1.

## What it does

1. **Sorting Service** (`src/sorting_service/sorter.py`) listens for inspection results, decides the bin, and publishes a sort command.
2. **Device Simulator** (`src/sorting_service/simulator.py`) listens for sort commands, simulates the diverter moving, and publishes its status.
3. **Retry logic**: if the device reports `ERROR`, the Sorting Service resends the command up to 2 times. If it still fails, the product is redirected to the review bin. If even that fails, an error is published to `factory/system/error`.

## Topics

| Direction | Topic | Used by |
|---|---|---|
| Subscribe | `factory/inspection/result` | Sorting Service |
| Subscribe | `factory/device/+/status` | Sorting Service |
| Publish | `factory/sorter/command` | Sorting Service |
| Publish | `factory/system/error` | Sorting Service |
| Subscribe | `factory/sorter/command` | Simulator |
| Publish | `factory/device/<device_id>/status` | Simulator |

## Decision table

| Condition | Action | Bin |
|---|---|---|
| `status = pass` and `confidence >= 0.8` | `accept` | 1 |
| `status = fail` and `confidence >= 0.8` | `reject` | 2 |
| `confidence < 0.8` | `review` | 3 |
| Unknown status | `review` | 3 |

The threshold and bin numbers are constants at the top of `sorter.py`.

## Device states

| State | Meaning |
|---|---|
| `IDLE` | Waiting for a command |
| `MOVING` | Diverter is moving (about 1 second) |
| `DONE` | Product placed in the bin |
| `ERROR` | Random failure (20% chance) |

## Message examples

Sort command (published by the Sorting Service):

```json
{
  "message_id": "uuid",
  "product_id": "P-2001",
  "timestamp": "2026-11-24T11:09:20+00:00",
  "event_type": "sort_command",
  "data": {"action": "accept", "target_bin": 1},
  "source": "sorter-01"
}
```

Device status (published by the Simulator):

```json
{
  "message_id": "uuid",
  "product_id": "P-2001",
  "timestamp": "2026-11-24T11:09:21+00:00",
  "event_type": "device_status",
  "data": {"state": "online", "operation_state": "DONE", "target_bin": 1},
  "source": "diverter-01"
}
```

The `operation_state` field is an extension added to the `device_status` data. The `review` action is an extension added to the `sort_command` data.

## Robustness

- Malformed inspection data is logged and skipped, the service does not crash.
- Duplicate messages (same `message_id`) are ignored.
- MQTT reconnection is handled by the Subscriber from Member 1.

## How to run (Windows PowerShell)

Requirements: Docker Desktop, Python 3.10+, Git.

```
git clone https://github.com/abdelrahman-ahmed07/distributed-systems-sorting-simulation
cd distributed-systems-sorting-simulation
pip install -r requirements.txt
docker compose up -d
$env:PYTHONPATH = "src"
```

Then run each in its own PowerShell window:

```
python -m sorting_service.simulator
python -m sorting_service.sorter
python examples\test_decisions.py
```

## How to test

```
$env:PYTHONPATH = "src"
python -m pytest tests -v
```

Result: 21 passed (10 from the MQTT layer, 11 for the Sorting Service).

## Notes for other members

- Member 2 (Database): store `product_id`, `action`, `target_bin`, and the final device state (`DONE` or `ERROR`).
- Member 4 (Integration): useful events for the WebSocket bridge are the sort command, the device status (`operation_state`), and `factory/system/error`.
## Credits
The MQTT communication layer (src/mqtt_service) was written by Member 1 (Amar Yasser). See README_MQTT.md.
