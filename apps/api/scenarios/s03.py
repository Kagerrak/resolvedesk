"""Post-implementation upload/API/PostgreSQL/worker scenarios; synthetic local data only."""

import base64
import os
from concurrent.futures import ThreadPoolExecutor

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.knowledge_worker import run_once
from resolvedesk.local_admin import grant

WEB = os.environ.get("SCENARIO_WEB_URL", "http://localhost:3000")
users, workspaces, checks = [], [], []


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


def visitor():
    client = httpx.Client(base_url=WEB, headers={"Origin": WEB}, timeout=20)
    response = client.post("/api/auth/sign-in/anonymous", json={})
    response.raise_for_status()
    user = response.json()["user"]["id"]
    users.append(user)
    w = client.post("/api/backend/demo").json()["id"]
    workspaces.append(w)
    return client, user, w


def upload(client, route, content, filename="guide.md"):
    return client.post(
        route,
        json={
            "title": "Synthetic access guide",
            "filename": filename,
            "content_base64": base64.b64encode(content).decode(),
        },
    )


try:
    a, ua, wa = visitor()
    b, ub, wb = visitor()
    route = f"/api/backend/workspaces/{wa}/knowledge"
    check(upload(a, route, b"Not authorized").status_code == 403, "Agent cannot upload knowledge")
    from uuid import UUID

    grant(UUID(wa))
    with engine.begin() as db:
        db.execute(
            text("INSERT INTO membership(workspace_id,user_id,role) VALUES(:w,:u,'viewer')"),
            {"w": wa, "u": ub},
        )
    check(
        upload(a, route, b"binary", "document.docx").status_code == 415,
        "Unsupported format rejected with format guidance",
    )
    check(
        upload(a, route, b"x" * (256 * 1024 + 1), "large.txt").status_code == 413,
        "Oversized text rejected by API",
    )
    check(upload(a, route, b"\xff\xfe").status_code == 422, "Invalid UTF-8 rejected")
    check(upload(a, route, b"  ").status_code == 422, "Empty document rejected")
    response = upload(
        a,
        route,
        b"# Project access\n\nProject membership is separate from workspace role.\n\n## Review\n\nAsk a project Admin to inspect membership.\n<script>unsafe()</script>",
    )
    response.raise_for_status()
    doc = response.json()
    path = f"{route}/{doc['id']}"
    check(
        doc["status"] == "queued" and doc["embedding_model"] == "fixture-hash-v1",
        "Upload persists queued source and explicit fixture model",
    )
    check(
        a.post(path + "/publish", json={"expected_revision": doc["revision"]}).status_code == 409,
        "Cannot publish incomplete indexing",
    )
    check(
        b.get(route).json() == [] and b.get(path).status_code == 404,
        "Viewer cannot inspect unpublished source",
    )
    check(
        a.get(f"/api/backend/workspaces/{wb}/knowledge/{doc['id']}").status_code == 404,
        "Cross-workspace source lookup reveals nothing",
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: run_once(), range(2)))
    detail = a.get(path).json()
    check(
        detail["status"] == "ready" and len(detail["sections"]) == 2,
        "Real worker parses headings into two persisted sections",
    )
    check(detail["job"]["attempts"] == 1, "Concurrent workers claim one job once")
    check(
        "<script>" in detail["sections"][1]["content"],
        "Source content remains inert plain text for escaped rendering",
    )
    with engine.connect() as db:
        vectors = (
            db.execute(
                text(
                    "SELECT vector_dims(embedding) FROM knowledge_chunk WHERE version_id=:v ORDER BY ordinal"
                ),
                {"v": doc["version_id"]},
            )
            .scalars()
            .all()
        )
    check(
        len(vectors) == 2 and all(dimensions == 64 for dimensions in vectors),
        "Fixture embedding ingestion persists 64-dimensional vectors",
    )
    check(
        a.post(path + "/publish", json={"expected_revision": doc["revision"]}).status_code == 409,
        "Worker progress invalidates stale Admin command",
    )
    check(
        b.post(path + "/publish", json={"expected_revision": detail["revision"]}).status_code
        == 403,
        "Viewer cannot publish",
    )
    published = a.post(path + "/publish", json={"expected_revision": detail["revision"]}).json()
    check(
        published["status"] == "published" and len(b.get(route).json()) == 1,
        "Published version becomes available to authorized readers",
    )
    check(
        b.get(path).json()["sections"] == detail["sections"],
        "Published source opens its actual persisted sections",
    )
    check(
        b.post(path + "/archive", json={"expected_revision": published["revision"]}).status_code
        == 403,
        "Viewer cannot archive",
    )
    archived = a.post(path + "/archive", json={"expected_revision": published["revision"]}).json()
    check(
        archived["archived"] and b.get(route).json() == [] and b.get(path).status_code == 404,
        "Archive removes source from published reads",
    )
    failed = upload(a, route, b"# Heading without readable body\n").json()
    failed_path = f"{route}/{failed['id']}"
    run_once()
    inspected = a.get(failed_path).json()
    check(
        inspected["status"] == "failed" and inspected["job"]["error"] and not inspected["sections"],
        "Failed parse exposes recovery and no partial sections",
    )
    for _ in range(2):
        check(
            a.post(
                failed_path + "/retry", json={"expected_revision": inspected["revision"]}
            ).status_code
            == 200,
            "Admin safely queues a failed job retry",
        )
        run_once()
        inspected = a.get(failed_path).json()
    check(
        inspected["job"]["attempts"] == 3
        and a.post(
            failed_path + "/retry", json={"expected_revision": inspected["revision"]}
        ).status_code
        == 409,
        "Retry budget stops repeated failing files after three attempts",
    )
    recovery = upload(a, route, b"A recoverable plain text source.", "recovery.txt").json()
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE knowledge_job SET status='processing', attempts=1, lease_token=gen_random_uuid(), lease_until=now()-interval '1 minute' WHERE version_id=:v"
            ),
            {"v": recovery["version_id"]},
        )
        db.execute(
            text("UPDATE document_version SET status='processing' WHERE id=:v"),
            {"v": recovery["version_id"]},
        )
    run_once()
    recovered = a.get(f"{route}/{recovery['id']}").json()
    check(
        recovered["status"] == "ready"
        and recovered["job"]["attempts"] == 2
        and len(recovered["sections"]) == 1,
        "Expired durable lease is recovered without duplicate sections",
    )
    with engine.connect() as db:
        original = db.scalar(
            text("SELECT content FROM document_version WHERE id=:v"), {"v": recovery["version_id"]}
        )
    check(
        original == "A recoverable plain text source.",
        "Original source is stored privately in PostgreSQL",
    )
    print(
        f"\n{len(checks)} assertions passed. Real HTTP, PostgreSQL and worker execution; no mocks."
    )
finally:
    with engine.begin() as db:
        for w in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": w})
        for u in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": u})
