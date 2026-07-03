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


def test_index_returns_html(client):
    response = client.get("/")
    assert b"<!DOCTYPE html>" in response.data


def test_index_references_reset_css(client):
    response = client.get("/")
    assert b"reset.css" in response.data


def test_reset_css_returns_200(client):
    response = client.get("/static/css/reset.css")
    assert response.status_code == 200


def test_reset_css_contains_reset_rules(client):
    response = client.get("/static/css/reset.css")
    assert b"margin: 0" in response.data
    assert b"padding: 0" in response.data


def test_nonexistent_route_returns_404(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
