"""Transaction CRUD, filtering and idempotency dedup."""

def _payload(**overrides):
    data = {
        "amount": 42.5,
        "type": "expense",
        "transaction_date": "2026-07-20T12:30:00",
        "merchant": "Starbucks",
        "description": "latte",
    }
    data.update(overrides)
    return data


def _create(client, **overrides):
    response = client.post("/api/v1/transactions", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_persisted_transaction(client):
    body = _create(client)
    assert body["amount"] == 42.5
    assert body["type"] == "expense"
    assert body["source"] == "manual"
    assert body["user_id"] == 1
    assert body["id"] > 0


def test_duplicate_create_returns_existing_row(client):
    first = _create(client)
    second = _create(client)
    assert second["id"] == first["id"]
    assert client.get("/api/v1/transactions").json()["total"] == 1


def test_dedup_ignores_surrounding_whitespace_and_case(client):
    """Spec: merchant/description are normalized before hashing."""
    first = _create(client, merchant="  Starbucks  ", description=" Latte ")
    second = _create(client, merchant="starbucks", description="latte")
    assert second["id"] == first["id"]


def test_list_pagination(client):
    for i in range(25):
        _create(
            client,
            amount=float(i + 1),
            transaction_date="2026-07-%02dT10:00:00" % (i % 28 + 1),
            merchant="shop-%d" % i,
            description="item-%d" % i,
        )

    page1 = client.get("/api/v1/transactions", params={"page": 1, "page_size": 10}).json()
    assert page1["total"] == 25
    assert len(page1["items"]) == 10
    assert page1["page"] == 1
    assert page1["page_size"] == 10

    page3 = client.get("/api/v1/transactions", params={"page": 3, "page_size": 10}).json()
    assert len(page3["items"]) == 5


def test_list_filter_by_type(client):
    _create(client, type="income", amount=5000)
    _create(client, type="expense", amount=20)

    income = client.get("/api/v1/transactions", params={"type": "income"}).json()
    assert income["total"] == 1
    assert income["items"][0]["amount"] == 5000


def test_list_filter_by_date_range(client):
    _create(client, transaction_date="2026-06-01T10:00:00")
    _create(client, transaction_date="2026-07-15T10:00:00")
    _create(client, transaction_date="2026-08-01T10:00:00")

    result = client.get(
        "/api/v1/transactions",
        params={"start_date": "2026-07-01T00:00:00", "end_date": "2026-07-31T23:59:59"},
    ).json()
    assert result["total"] == 1


def test_list_search_matches_merchant_or_description(client):
    _create(client, merchant="Luckin Coffee", description="americano")
    _create(client, merchant="Meituan", description="lunch")
    _create(client, merchant="Did", description="taxi")

    by_merchant = client.get("/api/v1/transactions", params={"search": "Luckin"}).json()
    assert by_merchant["total"] == 1

    by_description = client.get("/api/v1/transactions", params={"search": "taxi"}).json()
    assert by_description["total"] == 1


def test_get_one_and_missing(client):
    created = _create(client)
    fetched = client.get("/api/v1/transactions/%d" % created["id"])
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    assert client.get("/api/v1/transactions/99999").status_code == 404


def test_update_transaction(client):
    created = _create(client)
    updated = client.put(
        "/api/v1/transactions/%d" % created["id"],
        json=_payload(amount=99.9, merchant="New Merchant"),
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == 99.9
    assert updated.json()["merchant"] == "New Merchant"


def test_update_missing_transaction_returns_404(client):
    assert client.put("/api/v1/transactions/99999", json=_payload()).status_code == 404


def test_delete_transaction(client):
    created = _create(client)
    assert client.delete("/api/v1/transactions/%d" % created["id"]).status_code == 204
    assert client.get("/api/v1/transactions/%d" % created["id"]).status_code == 404
    assert client.delete("/api/v1/transactions/%d" % created["id"]).status_code == 404


def test_invalid_type_is_rejected(client):
    response = client.post("/api/v1/transactions", json=_payload(type="bogus"))
    assert response.status_code == 422


def test_page_size_upper_bound_is_enforced(client):
    response = client.get("/api/v1/transactions", params={"page_size": 101})
    assert response.status_code == 422


def test_negative_amount_is_stored_as_given(client):
    """Amounts are stored verbatim; the sign carries meaning for some sources."""
    body = _create(client, amount=-12.5)
    assert body["amount"] == -12.5
