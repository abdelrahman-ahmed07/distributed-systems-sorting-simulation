import json

import pytest

from mqtt_service import messages as m
from mqtt_service import topics


def test_build_message_has_all_required_fields():
    msg = m.build_message(m.INSPECTION_RESULT, {"status": "pass"}, product_id="P-1")
    for field in m.REQUIRED_FIELDS:
        assert field in msg


def test_message_ids_are_unique():
    a = m.build_message(m.SYSTEM_ERROR, {})
    b = m.build_message(m.SYSTEM_ERROR, {})
    assert a["message_id"] != b["message_id"]


def test_roundtrip():
    msg = m.build_message(m.SORT_COMMAND, {"action": "accept"}, product_id="P-2")
    assert m.parse_message(m.to_json(msg)) == msg


def test_parse_accepts_bytes():
    msg = m.build_message(m.DEVICE_STATUS, {"state": "online"})
    assert m.parse_message(m.to_json(msg).encode("utf-8"))["data"]["state"] == "online"


def test_invalid_json_rejected():
    with pytest.raises(m.InvalidMessageError):
        m.parse_message("not json")


def test_missing_fields_rejected():
    with pytest.raises(m.InvalidMessageError):
        m.parse_message(json.dumps({"message_id": "1"}))


def test_data_must_be_object():
    bad = m.build_message(m.SYSTEM_ERROR, {})
    bad["data"] = "text"
    with pytest.raises(m.InvalidMessageError):
        m.parse_message(json.dumps(bad))


def test_device_status_is_retained_others_are_not():
    assert topics.device_status("camera-01").retain is True
    assert topics.INSPECTION_RESULT.retain is False
    assert topics.SORTER_COMMAND.retain is False


def test_all_topics_use_qos_1():
    assert topics.INSPECTION_RESULT.qos == 1
    assert topics.SORTER_COMMAND.qos == 1
    assert topics.SYSTEM_ERROR.qos == 1
    