from fastapi.testclient import TestClient
import main


def reset():
    main.cart.clear(); main.idempotency.clear()
    for sku in main.SKUS.values():
        sku.stock = {"ocean-s": 4, "ocean-m": 1, "ocean-l": 0, "moss-s": 3, "moss-m": 2, "moss-l": 1, "clay-s": 2, "clay-m": 2}[sku.id]


def test_idempotent_cart_add():
    reset(); client = TestClient(main.app)
    first = client.post("/api/cart/items", json={"sku_id": "ocean-m", "quantity": 1}, headers={"Idempotency-Key": "a"})
    replay = client.post("/api/cart/items", json={"sku_id": "ocean-m", "quantity": 1}, headers={"Idempotency-Key": "a"})
    assert first.status_code == 201 and replay.json()["idempotent_replay"] is True
    assert client.get("/api/cart").json()["item_count"] == 1


def test_stock_cannot_be_oversold():
    reset(); client = TestClient(main.app)
    assert client.post("/api/cart/items", json={"sku_id": "ocean-m", "quantity": 1}, headers={"Idempotency-Key": "one"}).status_code == 201
    assert client.post("/api/cart/items", json={"sku_id": "ocean-m", "quantity": 1}, headers={"Idempotency-Key": "two"}).status_code == 409

