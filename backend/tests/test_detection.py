"""Detection engine: rules, statistical detector, pattern detector, fusion."""
import asyncio
from datetime import datetime

import polars as pl

from app.engine.detectors import (
    DetectionContext,
    PatternDetector,
    RuleDetector,
    StatisticalDetector,
)


def _add(client, amount, date="2026-07-20T12:00:00", type_="expense", merchant=None, description=None):
    payload = {
        "amount": amount,
        "type": type_,
        "transaction_date": date,
        "merchant": merchant or ("m-%s" % amount),
        "description": description or "txn",
    }
    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _run(client):
    response = client.post("/api/v1/detection/run")
    assert response.status_code == 200, response.text
    return response.json()


def _all_reasons(detections):
    return [reason for det in detections for reason in det["reason"]]


# --- Rule detector (integration through the API) ---

def test_large_expense_is_flagged_high(client):
    for i in range(5):
        _add(client, 20 + i, date="2026-07-1%dT10:00:00" % i)
    large = _add(client, 15000, date="2026-07-20T12:00:00", merchant="Furniture")

    _run(client)
    detections = client.get("/api/v1/detection").json()

    match = [d for d in detections if d["transaction_id"] == large["id"]]
    assert match, "large transaction was not flagged"
    assert match[0]["severity"] == "high"
    rule_ids = [r.get("rule_id") for r in match[0]["reason"]]
    assert "single_large_txn" in rule_ids
    assert match[0]["anomaly_score"] >= 0.8


def test_large_income_is_not_flagged_as_overspending(client):
    """单笔大额规则针对「消费」，工资等收入不应命中。"""
    _add(client, 20000, date="2026-07-20T12:00:00", type_="income", merchant="Employer")

    _run(client)
    detections = client.get("/api/v1/detection").json()
    rule_ids = [r.get("rule_id") for r in _all_reasons(detections)]
    assert "single_large_txn" not in rule_ids


def test_night_transaction_is_flagged_medium(client):
    night = _add(client, 30, date="2026-07-20T02:30:00", merchant="Night Bar")

    _run(client)
    detections = client.get("/api/v1/detection").json()

    match = [d for d in detections if d["transaction_id"] == night["id"]]
    assert match
    assert match[0]["severity"] in ("medium", "high")
    assert "night_txn" in [r.get("rule_id") for r in match[0]["reason"]]


def test_reasons_are_structured(client):
    _add(client, 15000)
    _run(client)
    detections = client.get("/api/v1/detection").json()
    assert detections
    for reason in _all_reasons(detections):
        assert "detector" in reason
        assert "detail" in reason


def test_detection_without_transactions_returns_zero(client):
    assert _run(client)["results_count"] == 0


def test_rerun_does_not_duplicate_results(client):
    _add(client, 15000)
    _run(client)
    first_count = len(client.get("/api/v1/detection").json())

    _run(client)
    second_count = len(client.get("/api/v1/detection").json())

    assert second_count == first_count, "重复检测产生了重复记录"


def test_mark_as_read_and_filter(client):
    _add(client, 15000)
    _run(client)
    detection = client.get("/api/v1/detection").json()[0]

    assert client.patch("/api/v1/detection/%d/read" % detection["id"]).status_code == 200
    assert client.get("/api/v1/detection", params={"is_read": True}).json()

    unread = client.get("/api/v1/detection", params={"is_read": False}).json()
    assert all(d["id"] != detection["id"] for d in unread)


def test_severity_filter(client):
    _add(client, 15000)
    _run(client)

    high = client.get("/api/v1/detection", params={"severity": "high"}).json()
    assert high and all(d["severity"] == "high" for d in high)

    assert client.get("/api/v1/detection", params={"severity": "nonsense"}).json() == []


def test_custom_rule_is_applied(client):
    """Settings 页创建的规则必须参与检测，否则只是摆设。"""
    created = client.post(
        "/api/v1/rules",
        json={
            "name": "超过 50 元",
            "condition": {"field": "amount", "operator": ">", "value": 50},
            "is_hard_rule": True,
            "is_enabled": True,
        },
    )
    assert created.status_code == 201

    txn = _add(client, 80, merchant="Small Shop")
    _run(client)

    detections = client.get("/api/v1/detection").json()
    assert any(d["transaction_id"] == txn["id"] for d in detections), "自定义规则未生效"


def test_disabled_rule_is_ignored(client):
    client.post(
        "/api/v1/rules",
        json={
            "name": "超过 50 元",
            "condition": {"field": "amount", "operator": ">", "value": 50},
            "is_hard_rule": True,
            "is_enabled": False,
        },
    )
    txn = _add(client, 80)
    _run(client)
    assert not any(
        d["transaction_id"] == txn["id"] for d in client.get("/api/v1/detection").json()
    )


# --- Detector units ---

def _frame(rows):
    return pl.DataFrame(rows)


def _context(df):
    return DetectionContext(user_id=1, transactions=df, budgets=[], global_baselines={})


def _row(i, amount, dt, category_id=1, merchant=None, description="txn"):
    return {
        "id": i,
        "user_id": 1,
        "amount": amount,
        "type": "expense",
        "category_id": category_id,
        "transaction_date": dt,
        "merchant": merchant,
        "description": description,
        "hour_bucket": dt.hour,
    }


def test_statistical_detector_skips_small_samples():
    df = _frame([_row(i, 10 + i, datetime(2026, 7, 10 + i, 12)) for i in range(4)])
    assert asyncio.run(StatisticalDetector().detect(df, _context(df))) == []


def test_statistical_detector_flags_outlier_in_larger_sample():
    rows = [_row(i, 10 + i, datetime(2026, 7, 10 + i, 12)) for i in range(9)]
    rows.append(_row(9, 9000, datetime(2026, 7, 19, 12)))
    df = _frame(rows)

    results = asyncio.run(StatisticalDetector().detect(df, _context(df)))
    flagged = {r.transaction_id for r in results}
    assert 9 in flagged


def test_pattern_detector_frequency_spike():
    rows = [
        _row(1, 10, datetime(2026, 7, 7, 12), category_id=1),
        _row(2, 10, datetime(2026, 7, 8, 12), category_id=10),
        _row(3, 10, datetime(2026, 7, 8, 12), category_id=11),
        _row(4, 10, datetime(2026, 7, 9, 12), category_id=12),
        _row(5, 10, datetime(2026, 7, 9, 12), category_id=13),
        _row(6, 10, datetime(2026, 7, 9, 12), category_id=14),
        _row(7, 10, datetime(2026, 7, 14, 12), category_id=1),
        _row(8, 10, datetime(2026, 7, 15, 12), category_id=1),
        _row(9, 10, datetime(2026, 7, 16, 12), category_id=1),
        _row(10, 10, datetime(2026, 7, 17, 12), category_id=2),
        _row(11, 10, datetime(2026, 7, 18, 12), category_id=3),
        _row(12, 10, datetime(2026, 7, 21, 12), category_id=4),
    ]
    df = _frame(rows)

    results = asyncio.run(PatternDetector().detect(df, _context(df)))
    methods = [r["method"] for res in results for r in res.reason]
    assert "frequency_spike" in methods


def test_pattern_detector_new_merchant():
    rows = []
    for i in range(6):
        rows.append(_row(i + 1, 10, datetime(2026, 7, 6 + i, 12), category_id=20 + i, merchant="Known%d" % i))
    for i in range(4):
        rows.append(_row(10 + i, 10, datetime(2026, 7, 16 + i, 12), category_id=i + 1))
    rows.append(_row(20, 10, datetime(2026, 7, 20, 12), category_id=7, merchant="BrandNew"))
    df = _frame(rows)

    results = asyncio.run(PatternDetector().detect(df, _context(df)))
    methods = [r["method"] for res in results for r in res.reason]
    assert "new_merchant" in methods


def test_pattern_detector_subscription_price_jump():
    amounts = [10] * 10 + [1000]
    rows = [
        _row(i + 1, amount, datetime(2026, 7, 1 + i, 12), category_id=8, description="视频会员")
        for i, amount in enumerate(amounts)
    ]
    df = _frame(rows)

    results = asyncio.run(PatternDetector().detect(df, _context(df)))
    methods = [r["method"] for res in results for r in res.reason]
    assert "subscription_spike" in methods


def test_rule_detector_hard_rule_weight_is_full():
    df = _frame([_row(1, 15000, datetime(2026, 7, 20, 12))])
    results = asyncio.run(RuleDetector().detect(df, _context(df)))
    assert any(r.anomaly_score == 1.0 and r.severity == "high" for r in results)
