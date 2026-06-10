"""Tests for the static dashboard and service banner routes."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_dashboard_html() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "InsightOps AI" in resp.text


def test_api_banner_moved() -> None:
    resp = client.get("/api")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dashboard"] == "/"
    assert "version" in body


def test_static_assets_served() -> None:
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
