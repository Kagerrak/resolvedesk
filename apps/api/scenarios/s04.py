"""Real HTTP, private PostgreSQL storage and isolated PDF-worker verification."""

import base64
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.knowledge_worker import run_once
from resolvedesk.local_admin import grant

WEB = "http://localhost:3000"
FIXTURES = Path(__file__).parent / "fixtures"
users, workspaces, checks = [], [], []


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


def visitor():
    client = httpx.Client(base_url=WEB, headers={"Origin": WEB}, timeout=30)
    response = client.post("/api/auth/sign-in/anonymous", json={})
    response.raise_for_status()
    user = response.json()["user"]["id"]
    users.append(user)
    response = client.post("/api/backend/demo")
    response.raise_for_status()
    workspace = response.json()["id"]
    workspaces.append(workspace)
    return client, user, workspace


def upload(client, route, raw, filename="guide.pdf"):
    return client.post(
        route,
        json={
            "title": "Synthetic PDF guide",
            "filename": filename,
            "content_base64": base64.b64encode(raw).decode(),
        },
    )


try:
    admin, ua, wa = visitor()
    viewer, uv, wv = visitor()
    grant(UUID(wa))
    with engine.begin() as db:
        db.execute(
            text("INSERT INTO membership(workspace_id,user_id,role) VALUES(:w,:u,'viewer')"),
            {"w": wa, "u": uv},
        )
    route = f"/api/backend/workspaces/{wa}/knowledge"
    original = (FIXTURES / "access-guide.pdf").read_bytes()
    check(upload(viewer, route, original).status_code == 403, "Viewer cannot upload PDF")
    check(upload(admin, route, b"not a pdf").status_code == 422, "False PDF signature rejected")
    check(
        upload(admin, route, b"%PDF-" + b"x" * (2 * 1024 * 1024)).status_code == 413,
        "PDF byte limit enforced through real proxy",
    )
    response = upload(admin, route, original)
    response.raise_for_status()
    doc = response.json()
    path = f"{route}/{doc['id']}"
    check(
        admin.get(path + "/download").content == original, "Admin downloads exact private original"
    )
    check(
        viewer.get(path + "/download").status_code == 404, "Unpublished original hidden from Viewer"
    )
    check(
        admin.get(f"/api/backend/workspaces/{wv}/knowledge/{doc['id']}/download").status_code
        == 404,
        "Original download enforces workspace isolation",
    )
    run_once()
    detail = admin.get(path).json()
    check(
        detail["status"] == "ready" and detail["page_count"] == 2,
        "Isolated parser persists two-page PDF",
    )
    check(
        {s["page_number"] for s in detail["sections"]} == {1, 2},
        "Every persisted passage retains its PDF page",
    )
    check(
        all(
            "Recovery steps" not in s["content"]
            for s in detail["sections"]
            if s["page_number"] == 1
        ),
        "Passage boundaries never cross pages",
    )
    with engine.connect() as db:
        row = db.execute(
            text("SELECT source_bytes, content, page_count FROM document_version WHERE id=:v"),
            {"v": doc["version_id"]},
        ).one()
    check(
        bytes(row.source_bytes) == original and row.content == "" and row.page_count == 2,
        "Original binary and page metadata persist privately in PostgreSQL",
    )
    published = admin.post(path + "/publish", json={"expected_revision": detail["revision"]})
    published.raise_for_status()
    download = viewer.get(path + "/download")
    check(
        download.content == original
        and "attachment" in download.headers["content-disposition"]
        and download.headers["x-content-type-options"] == "nosniff"
        and download.headers["content-security-policy"] == "sandbox",
        "Published original downloads as inert attachment with exact bytes",
    )
    check(
        viewer.get(path).json()["sections"] == detail["sections"],
        "Published page citations survive authenticated reload",
    )
    admin.post(
        path + "/archive", json={"expected_revision": published.json()["revision"]}
    ).raise_for_status()
    check(viewer.get(path + "/download").status_code == 404, "Archive revokes original download")
    for filename, raw, expected in [
        ("scanned.pdf", (FIXTURES / "scanned.pdf").read_bytes(), "no extractable text"),
        ("encrypted.pdf", (FIXTURES / "encrypted.pdf").read_bytes(), "Encrypted"),
        ("too-many-pages.pdf", (FIXTURES / "too-many-pages.pdf").read_bytes(), "1 to 20"),
        ("malformed.pdf", b"%PDF-1.7\ninvalid structure", "safely read"),
    ]:
        response = upload(admin, route, raw, filename)
        response.raise_for_status()
        bad_path = f"{route}/{response.json()['id']}"
        run_once()
        bad = admin.get(bad_path).json()
        check(
            bad["status"] == "failed" and expected in bad["job"]["error"] and not bad["sections"],
            f"{filename}: actionable failure with no partial indexing",
        )
        check(
            admin.post(
                bad_path + "/publish", json={"expected_revision": bad["revision"]}
            ).status_code
            == 409,
            f"{filename}: failed PDF cannot be published",
        )
    print(f"\n{len(checks)} assertions passed. Real HTTP/PostgreSQL/PDF subprocess; no mocks.")
finally:
    with engine.begin() as db:
        for workspace in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": workspace})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
