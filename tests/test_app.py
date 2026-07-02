import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_html(client):
    response = client.get("/")
    data = response.data.decode()
    assert "<!DOCTYPE html>" in data
    assert "reset.css" in data


def test_reset_css_returns_200(client):
    response = client.get("/static/css/reset.css")
    assert response.status_code == 200
    data = response.data.decode()
    assert "margin: 0" in data
    assert "padding: 0" in data


def test_nonexistent_route_returns_404(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
