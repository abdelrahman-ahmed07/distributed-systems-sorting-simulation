import pytest
from sorting_service import sorter


def insp(mid, pid, status, confidence):
    return {"message_id": mid, "product_id": pid,
            "data": {"status": status, "confidence": confidence}}


def dev(mid, pid, state):
    return {"message_id": mid, "product_id": pid,
            "data": {"operation_state": state}}


@pytest.fixture
def sent(monkeypatch):
    """يفضّي الحالة ويسجّل الأوامر بدل ما يبعتها فعلاً."""
    sorter.seen_ids.clear()
    sorter.pending.clear()
    log = []
    monkeypatch.setattr(sorter, "send_command",
                        lambda pid, action, b: log.append((pid, action, b)))
    monkeypatch.setattr(sorter.pub, "publish",
                        lambda *a, **k: log.append(("error",)))
    return log


def test_accept():
    assert sorter.decide({"status": "pass", "confidence": 0.97}) == ("accept", 1)


def test_reject():
    assert sorter.decide({"status": "fail", "confidence": 0.95}) == ("reject", 2)


def test_review_low_confidence():
    assert sorter.decide({"status": "pass", "confidence": 0.60}) == ("review", 3)


def test_threshold_boundary():
    assert sorter.decide({"status": "pass", "confidence": 0.80}) == ("accept", 1)
    assert sorter.decide({"status": "pass", "confidence": 0.79}) == ("review", 3)


def test_unknown_status_goes_to_review():
    assert sorter.decide({"status": "weird", "confidence": 0.99}) == ("review", 3)


def test_missing_field_raises():
    with pytest.raises(KeyError):
        sorter.decide({"status": "pass"})


def test_bad_data_does_not_crash(sent):
    sorter.on_inspection("t", {"message_id": "m1", "product_id": "P1", "data": {}})
    assert sent == []
    assert sorter.pending == {}


def test_duplicate_message_ignored(sent):
    msg = insp("m1", "P1", "pass", 0.97)
    sorter.on_inspection("t", msg)
    sorter.on_inspection("t", msg)
    assert sent == [("P1", "accept", 1)]


def test_done_clears_pending(sent):
    sorter.on_inspection("t", insp("m1", "P1", "pass", 0.97))
    sorter.on_device_status("t", dev("m2", "P1", "DONE"))
    assert "P1" not in sorter.pending


def test_retry_twice_then_review(sent):
    sorter.on_inspection("t", insp("m1", "P1", "pass", 0.97))
    sorter.on_device_status("t", dev("m2", "P1", "ERROR"))
    sorter.on_device_status("t", dev("m3", "P1", "ERROR"))
    sorter.on_device_status("t", dev("m4", "P1", "ERROR"))
    assert sent == [("P1", "accept", 1)] * 3 + [("P1", "review", 3)]


def test_failure_even_in_review_reports_error(sent):
    sorter.on_inspection("t", insp("m1", "P1", "pass", 0.97))
    for i in range(2, 6):
        sorter.on_device_status("t", dev("m%d" % i, "P1", "ERROR"))
    assert sent[-1] == ("error",)
    assert "P1" not in sorter.pending