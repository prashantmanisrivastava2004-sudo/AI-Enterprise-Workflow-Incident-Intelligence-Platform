from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_analyze_ticket():
    response = client.post(
        "/analyze-ticket",
        json={
            "ticket": "My laptop cannot connect to the office Wi-Fi.",
            "type": "Incident"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "ticket" in data
    assert "category" in data
    assert "queue" in data
    assert "priority" in data
    assert "retrieved_incidents" in data


def test_missing_ticket():
    response = client.post(
        "/analyze-ticket",
        json={
            "type": "Incident"
        }
    )

    assert response.status_code == 422