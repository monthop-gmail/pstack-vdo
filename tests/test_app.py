"""Smoke test — บูต pstack + vdo_addons บน sqlite

pstack ต้องอยู่ที่ ../pstack หรือ ./pstack_src (CI) หรือ override ด้วย env:
    PSTACK_ADDONS_PATHS=<path-ของ-pstack>/addons,vdo_addons
"""

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "PSTACK_ADDONS_PATHS" not in os.environ:
    for candidate in (ROOT / "pstack_src", ROOT.parent / "pstack", ROOT.parent / "test-pstack"):
        if (candidate / "addons").is_dir():
            os.environ["PSTACK_ADDONS_PATHS"] = f"{candidate / 'addons'},vdo_addons"
            sys.path.insert(0, str(candidate))  # ให้ import core ได้แม้ยังไม่ pip install
            break

os.environ["PSTACK_DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"
os.environ["PSTACK_SECRET_KEY"] = "test-secret"
os.environ["PSTACK_MODULES"] = "users,storage,vdo"
os.environ["PSTACK_STORAGE_DIR"] = "./test_uploads"
os.environ["PSTACK_VDO_HLS_DIR"] = "./test_hls"

import pytest
from fastapi.testclient import TestClient

from core.app import create_app


@pytest.fixture(scope="module")
def client():
    import shutil

    paths = [
        pathlib.Path("./test_app.db"),
        pathlib.Path("./test_uploads"),
        pathlib.Path("./test_hls"),
    ]

    def cleanup():
        for p in paths:
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()

    cleanup()
    app = create_app()
    with TestClient(app) as c:
        yield c
    cleanup()


@pytest.fixture(scope="module")
def auth(client):
    token = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "admin"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_boot_with_pstack(client):
    modules = client.get("/healthz").json()["modules"]
    assert {"users", "storage", "vdo"} <= set(modules)


def test_upload_video(client, auth):
    r = client.post(
        "/api/vdo/videos",
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
        data={"title": "คลิปทดสอบ"},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    video = r.json()
    assert video["title"] == "คลิปทดสอบ"
    # ไม่มี redis ในเทส -> enqueue ไม่ได้ ค้างที่ uploaded (มี redis จะเป็น processing)
    assert video["status"] in ("uploaded", "processing")

    # list + get
    assert any(v["id"] == video["id"] for v in client.get("/api/vdo/videos", headers=auth).json())
    assert client.get(f"/api/vdo/videos/{video['id']}", headers=auth).json()["id"] == video["id"]


def test_vdo_tools_registered(client):
    from core.ai import get_tools

    names = {t.name: t for t in get_tools(["vdo"])}
    assert "search_videos" in names
    assert names["search_videos"].permission is None  # สาธารณะ
    assert names["video_pipeline_status"].permission == "vdo.manage"


def test_transcode_job_registered(client):
    from core.jobs import _jobs

    assert "transcode_video" in _jobs


def test_hls_route_not_found(client):
    assert client.get("/hls/999/index.m3u8").status_code == 404
    # path traversal โดนกัน
    assert client.get("/hls/1/..%2F..%2Fetc%2Fpasswd").status_code == 404
