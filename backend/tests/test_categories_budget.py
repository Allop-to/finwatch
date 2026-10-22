"""Category tree and budget progress calculations."""


def _create_txn(client, amount, date, category_id=None, type_="expense"):
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": amount,
            "type": type_,
            "transaction_date": date,
            "category_id": category_id,
            "merchant": "merchant-%s" % amount,
            "description": "txn",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- Categories ---

def test_category_tree_matches_seed_data(client):
    cats = client.get("/api/v1/categories").json()

    assert len(cats) == 10, "expected 10 top-level system categories"
    total = sum(1 + len(c["children"]) for c in cats)
    assert total == 27, "seed file contains 10 parents + 17 children"

    dining = next(c for c in cats if c["name"] == "餐饮")
    assert [c["name"] for c in dining["children"]] == ["咖啡饮品", "正餐", "外卖"]


def test_system_categories_are_flagged(client):
    cats = client.get("/api/v1/categories").json()
    assert all(c["is_system"] for c in cats)
    assert all(child["is_system"] for c in cats for child in c["children"])


def test_create_and_delete_custom_category(client):
    created = client.post("/api/v1/categories", json={"name": "宠物", "icon": "🐱"})
    assert created.status_code == 201
    body = created.json()
    assert body["is_system"] is False

    listed = client.get("/api/v1/categories").json()
    assert any(c["name"] == "宠物" for c in listed)

    assert client.delete("/api/v1/categories/%d" % body["id"]).status_code == 204
    assert not any(c["name"] == "宠物" for c in client.get("/api/v1/categories").json())


def test_system_category_cannot_be_deleted(client):
    cats = client.get("/api/v1/categories").json()
    assert client.delete("/api/v1/categories/%d" % cats[0]["id"]).status_code == 404


# --- Budgets ---

def _create_budget(client, **overrides):
    payload = {
        "amount_limit": 1000,
        "period": "monthly",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "alert_threshold": 0.8,
    }
    payload.update(overrides)
    response = client.post("/api/v1/budgets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_budget_progress_without_transactions_is_zero(client):
    budget = _create_budget(client)
    assert budget["spent_amount"] == 0
    assert budget["progress_pct"] == 0


def test_budget_progress_counts_expenses_in_range(client):
    _create_txn(client, 200, "2026-07-10T12:00:00")
    _create_txn(client, 300, "2026-07-20T12:00:00")
    _create_txn(client, 999, "2026-06-10T12:00:00")  # outside period
    _create_txn(client, 555, "2026-07-15T12:00:00", type_="income")  # income ignored

    budget = _create_budget(client)
    assert budget["spent_amount"] == 500
    assert budget["progress_pct"] == 50.0


def test_budget_includes_transactions_on_end_date(client):
    """A budget ending 2026-07-31 must cover the whole day."""
    _create_txn(client, 250, "2026-07-31T12:00:00")

    budget = _create_budget(client)
    assert budget["spent_amount"] == 250
    assert budget["progress_pct"] == 25.0


def test_category_budget_only_counts_that_category(client):
    cats = client.get("/api/v1/categories").json()
    dining = next(c for c in cats if c["name"] == "餐饮")
    coffee = next(c for c in dining["children"] if c["name"] == "咖啡饮品")
    transport = next(c for c in cats if c["name"] == "交通")
    taxi = next(c for c in transport["children"] if c["name"] == "打车")

    _create_txn(client, 100, "2026-07-10T10:00:00", category_id=coffee["id"])
    _create_txn(client, 400, "2026-07-11T10:00:00", category_id=taxi["id"])

    budget = _create_budget(client, category_id=coffee["id"], amount_limit=500)
    assert budget["spent_amount"] == 100
    assert budget["progress_pct"] == 20.0


def test_budget_list_and_delete(client):
    budget = _create_budget(client)
    listed = client.get("/api/v1/budgets").json()
    assert len(listed) == 1
    assert listed[0]["id"] == budget["id"]

    assert client.delete("/api/v1/budgets/%d" % budget["id"]).status_code == 204
    assert client.get("/api/v1/budgets").json() == []
    assert client.delete("/api/v1/budgets/%d" % budget["id"]).status_code == 404
