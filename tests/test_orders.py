from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

def test_create_order():
    response = client.post(
        "/api/v1/order",
        headers={"Authorization": "TOVALIDKEY"},
        json={"ticker": "MEMCOIN", "type": "LIMIT", "price": 100, "qty": 5}
    )

    assert response.status_code == 200