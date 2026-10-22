"""Misc endpoints: health, detection rules CRUD, data management, websocket."""


# --- Health ---

def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["app"]


# --- Detection rules CRUD ---

def test_rule_crud_cycle(client):
    created = client.post(
        "/api/v1/rules",
        json={"name": "午夜空窗", "condition": {"field": "hour", "operator": "in", "value": [2]}},
    )
    assert created.status_code == 201, created.text
    rule = created.json()
    assert rule["is_hard_rule"] is False
    assert rule["is_enabled"] is True

    assert [r["id"] for r in client.get("/api/v1/rules").json()] == [rule["id"]]

    updated = client.put(
        "/api/v1/rules/%d" % rule["id"],
        json={"name": "午夜空窗 v2", "is_enabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "午夜空窗 v2"
    assert updated.json()["is_enabled"] is False
    assert updated.json()["condition"] == rule["condition"]

    assert client.delete("/api/v1/rules/%d" % rule["id"]).status_code == 204
    assert client.get("/api/v1/rules").json() == []


def test_update_unknown_rule_returns_404(client):
    assert client.put("/api/v1/rules/999", json={"name": "x"}).status_code == 404
    assert client.delete("/api/v1/rules/999").status_code == 404


def test_seed_defaults_is_idempotent(client):
    first = client.post("/api/v1/rules/seed-defaults").json()
    assert first["count"] == 3

    second = client.post("/api/v1/rules/seed-defaults").json()
    assert second["count"] == 3
    assert len(client.get("/api/v1/rules").json()) == 3


# --- Data management ---

def _txn(client, amount=100):
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": amount,
            "type": "expense",
            "transaction_date": "2026-07-20T12:00:00",
            "merchant": "shop",
        },
    )
    assert response.status_code == 201, response.text


def test_data_stats_counts(client):
    _txn(client, amount=15000)  # large enough to trigger a detection
    client.post("/api/v1/detection/run")

    stats = client.get("/api/v1/rules/data/stats").json()
    assert stats["transactions"] == 1
    assert stats["detections"] == 1
    assert stats["budgets"] == 0


def test_data_stats_reports_seeded_categories(client):
    """分类是系统种子数据，数据统计页不应显示 0 个分类。"""
    stats = client.get("/api/v1/rules/data/stats").json()
    listed = client.get("/api/v1/categories").json()
    total = sum(1 + len(c["children"]) for c in listed)
    assert stats["categories"] == total, "统计分类数为 %s，实际有 %s 个" % (stats["categories"], total)


def test_export_csv(client):
    _txn(client)
    response = client.get("/api/v1/rules/data/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "finwatch_export.csv" in response.headers["content-disposition"]

    lines = response.text.lstrip("\ufeff").strip().splitlines()
    assert lines[0].startswith("日期,类型,金额")
    assert len(lines) == 2
    assert "100" in lines[1]


def test_export_csv_is_utf8_with_bom_for_excel(client):
    """Excel 打开无 BOM 的 UTF-8 CSV 会乱码。"""
    _txn(client)
    response = client.get("/api/v1/rules/data/export")
    assert response.content.startswith(b"\xef\xbb\xbf"), "导出 CSV 缺少 UTF-8 BOM"


def test_clear_detections(client):
    _txn(client, amount=15000)
    client.post("/api/v1/detection/run")
    assert client.get("/api/v1/detection").json()

    response = client.post("/api/v1/rules/data/clear-detections")
    assert response.status_code == 200
    assert client.get("/api/v1/detection").json() == []
    assert client.get("/api/v1/transactions").json()["total"] == 1


def test_clear_all_keeps_system_categories(client):
    _txn(client)
    client.post("/api/v1/budgets", json={
        "amount_limit": 100,
        "period": "monthly",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
    })
    client.post("/api/v1/categories", json={"name": "自定义"})
    client.post("/api/v1/rules/data/clear-all")

    assert client.get("/api/v1/transactions").json()["total"] == 0
    assert client.get("/api/v1/budgets").json() == []
    assert len(client.get("/api/v1/categories").json()) == 10
    assert not any(c["name"] == "自定义" for c in client.get("/api/v1/categories").json())


# --- WebSocket ---

def test_websocket_heartbeat(client):
    with client.websocket_connect("/api/v1/ws") as ws:
        ws.send_text("ping")
        assert ws.receive_json() == {"type": "system.health", "data": "ok"}
