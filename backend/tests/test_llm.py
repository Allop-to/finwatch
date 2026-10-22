"""LLM integration: offline fallback, persistence of explanations, limits."""
from app.services import llm_service
from app.services.llm_service import RateLimiter, _hardcoded_fallback, _render_fallback


def _detection_id(client):
    client.post(
        "/api/v1/transactions",
        json={
            "amount": 15000,
            "type": "expense",
            "transaction_date": "2026-07-20T12:00:00",
            "merchant": "Furniture",
        },
    )
    client.post("/api/v1/detection/run")
    return client.get("/api/v1/detection").json()[0]["id"]


def test_template_fallback_renders_rule_reason():
    text = _render_fallback(
        "anomaly_explanation.md",
        severity_emoji="🔴",
        severity_text="高危",
        detector_type="rule",
        reasons=[{"rule_id": "single_large_txn"}],
        amount=15000,
        time_context="中午",
        suggestions=[],
    )
    assert "检测到高危异常消费" in text
    assert "15000.00" in text
    assert "建议" in text


def test_hardcoded_fallback_uses_real_newlines():
    text = _hardcoded_fallback(severity="high", amount=100)
    assert "\n" in text
    assert "\\n" not in text, "兜底文案输出了字面量 \\n"


def test_explain_without_llm_returns_fallback(client):
    detection_id = _detection_id(client)
    response = client.post("/api/v1/llm/explain", json={"detection_id": detection_id})
    assert response.status_code == 200, response.text
    assert response.json()["explanation"].strip()


def test_explanation_is_persisted_to_detection(client):
    detection_id = _detection_id(client)
    explanation = client.post(
        "/api/v1/llm/explain", json={"detection_id": detection_id}
    ).json()["explanation"]

    stored = client.get("/api/v1/detection/%d" % detection_id).json()
    assert stored["suggestion"] == explanation


def test_explain_unknown_detection_returns_404(client):
    assert client.post("/api/v1/llm/explain", json={"detection_id": 99999}).status_code == 404


def test_chat_without_llm_returns_offline_message(client):
    response = client.post("/api/v1/llm/chat", json={"message": "本月花了多少？"})
    assert response.status_code == 200, response.text
    assert "暂时不可用" in response.json()["reply"]


def test_usage_reports_limits(client):
    usage = client.get("/api/v1/llm/usage").json()
    assert usage["llm_enabled"] is False
    assert usage["chat"]["limit"] == 30
    assert usage["auto_explain"]["limit"] == 10


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(auto_explain_limit=2, chat_limit=1)
    assert limiter.can_auto_explain()
    limiter.record_auto()
    limiter.record_auto()
    assert not limiter.can_auto_explain()

    assert limiter.can_chat()
    limiter.record_chat()
    assert not limiter.can_chat()
