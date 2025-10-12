from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_and_get_item():
    res = client.post("/items", json={"name": "Hello"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1 and data["name"] == "Hello"

    res2 = client.get(f"/items/{data['id']}")
    assert res2.status_code == 200
    assert res2.json() == data


def test_list_items():
    client.post("/items", json={"name": "A"})
    client.post("/items", json={"name": "B"})
    res = client.get("/items?limit=1&offset=1")
    assert res.status_code == 200
    assert len(res.json()) == 1
