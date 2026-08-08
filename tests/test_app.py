"""Smoke test — บูต pstack + addons ของ app นี้บน sqlite

pstack ต้องอยู่ที่ ../pstack หรือ ./pstack_src (CI) หรือ override ด้วย env:
    PSTACK_ADDONS_PATHS=<path-ของ-pstack>/addons,app_addons
"""

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "PSTACK_ADDONS_PATHS" not in os.environ:
    for candidate in (ROOT / "pstack_src", ROOT.parent / "pstack"):
        if (candidate / "addons").is_dir():
            os.environ["PSTACK_ADDONS_PATHS"] = f"{candidate / 'addons'},app_addons"
            sys.path.insert(0, str(candidate))  # ให้ import core ได้แม้ยังไม่ pip install
            break

os.environ["PSTACK_DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"
os.environ["PSTACK_SECRET_KEY"] = "test-secret"
os.environ["PSTACK_MODULES"] = "users,demo"

import pytest
from fastapi.testclient import TestClient

from core.app import create_app


@pytest.fixture(scope="module")
def client():
    db_file = pathlib.Path("./test_app.db")
    if db_file.exists():
        db_file.unlink()
    app = create_app()
    with TestClient(app) as c:
        yield c
    if db_file.exists():
        db_file.unlink()


def test_boot_with_pstack(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert "users" in r.json()["modules"]
    assert "demo" in r.json()["modules"]


def test_demo_module(client):
    assert client.get("/api/demo/ping").json()["status"] == "ok"


def test_pstack_auth_works(client):
    r = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "admin"}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["email"] == "admin@example.com"
