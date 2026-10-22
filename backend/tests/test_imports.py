"""CSV import pipeline: parsing, direction, dedup and traceability."""
ALIPAY_CSV = (
    "交易时间,收/支,交易对方,商品说明,金额\n"
    "2026-07-20 12:30:00,支出,xx拉面,午餐,42.00\n"
    "2026-07-19 18:00:00,支出,滴滴出行,打车,28.50\n"
)

WECHAT_CSV = (
    "交易时间,交易类型,交易对方,商品,收/支,金额(元)\n"
    "2026-07-20 12:30:00,商户消费,美团外卖,午餐,支出,35.00\n"
    "2026-07-18 09:00:00,转账,张三,转账,收入,100.00\n"
)


def _upload(client, content, source_type="alipay", filename="bill.csv", encoding="utf-8"):
    return client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content.encode(encoding), "text/csv")},
        data={"source_type": source_type},
    )


def test_alipay_csv_import_counts(client):
    response = _upload(client, ALIPAY_CSV)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "done"
    assert body["row_count"] == 2
    assert body["new_count"] == 2
    assert body["skipped_count"] == 0


def test_alipay_expense_direction_is_respected(client):
    """支付宝账单中金额恒为正，方向由「收/支」列决定。"""
    _upload(client, ALIPAY_CSV)
    items = client.get("/api/v1/transactions").json()["items"]
    assert len(items) == 2
    assert {t["type"] for t in items} == {"expense"}


def test_reupload_is_deduplicated(client):
    first = _upload(client, ALIPAY_CSV).json()
    second = _upload(client, ALIPAY_CSV).json()

    assert second["new_count"] == 0
    assert second["skipped_count"] == 2
    assert first["import_id"] != second["import_id"]
    assert client.get("/api/v1/transactions").json()["total"] == 2


def test_wechat_csv_import(client):
    response = _upload(client, WECHAT_CSV, source_type="wechat", filename="wechat.csv")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["new_count"] == 2

    items = client.get("/api/v1/transactions").json()["items"]
    by_merchant = {t["merchant"]: t for t in items}
    assert by_merchant["美团外卖"]["type"] == "expense"
    assert by_merchant["张三"]["type"] == "income"


def test_amount_with_thousand_separator(client):
    csv_content = (
        "交易时间,收/支,交易对方,商品说明,金额\n"
        "2026-07-20 12:30:00,支出,家具城,沙发,\"12,800.00\"\n"
    )
    response = _upload(client, csv_content)
    assert response.status_code == 200, response.text

    items = client.get("/api/v1/transactions").json()["items"]
    assert items[0]["amount"] == 12800.0


def test_unsupported_source_type_is_rejected(client):
    response = _upload(client, ALIPAY_CSV, source_type="paypal")
    assert response.status_code == 400


def test_imported_transactions_link_to_import_record(client):
    """import_id exists for source traceability and must be populated."""
    body = _upload(client, ALIPAY_CSV).json()
    items = client.get("/api/v1/transactions").json()["items"]
    assert all(t["import_id"] == body["import_id"] for t in items)


def test_import_history_is_listed(client):
    _upload(client, ALIPAY_CSV)
    history = client.get("/api/v1/imports").json()
    assert len(history) == 1
    assert history[0]["source_type"] == "alipay"
    assert history[0]["status"] == "done"


def test_gbk_encoded_csv_is_handled(lenient_client):
    """支付宝导出的 CSV 通常是 GBK 编码，不应直接 500。"""
    response = _upload(lenient_client, ALIPAY_CSV, encoding="gbk")
    assert response.status_code != 500, "GBK 文件导致服务器 500: %s" % response.text


def test_empty_csv_is_accepted(client):
    response = _upload(client, "交易时间,收/支,交易对方,商品说明,金额\n")
    assert response.status_code == 200
    assert response.json()["row_count"] == 0
