"""Post-implementation real HTTP/PostgreSQL/workers: operational recovery and source erasure."""

import base64
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.generation import run_once as generate_once
from resolvedesk.knowledge_worker import run_once as index_once
from resolvedesk.local_admin import grant

WEB = "http://localhost:3000"
users, workspaces, checks = [], [], []


def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label, flush=True)


def visitor():
    client = httpx.Client(
        base_url=WEB,
        headers={"Origin": WEB},
        timeout=30,
        event_hooks={"response": [lambda _: time.sleep(1.1)]},
    )
    r = client.post("/api/auth/sign-in/anonymous", json={})
    r.raise_for_status()
    u = r.json()["user"]["id"]
    users.append(u)
    r = client.post("/api/backend/demo")
    r.raise_for_status()
    w = r.json()["id"]
    workspaces.append(w)
    t = client.get(f"/api/backend/workspaces/{w}/tickets").json()[0]["id"]
    return client, u, w, t


def sql(statement, **values):
    with engine.begin() as db:
        return db.execute(text(statement), values)


try:
    a, ua, wa, ta = visitor()
    b, ub, wb, tb = visitor()
    root = f"/api/backend/workspaces/{wa}"
    ticket = root + f"/tickets/{ta}"
    grant(wa)

    def upload(content, title="Synthetic recovery source", filename="recovery.md"):
        r = a.post(
            root + "/knowledge",
            json={
                "title": title,
                "filename": filename,
                "content_base64": base64.b64encode(content).decode(),
            },
        )
        r.raise_for_status()
        return r.json()

    def doc(source):
        r = a.get(root + f"/knowledge/{source['id']}")
        r.raise_for_status()
        return r.json()

    def activity(**params):
        r = a.get(root + "/activity", params=params)
        r.raise_for_status()
        return r.json()

    def operation(source):
        return next(
            row for row in activity(kind="indexing")["items"] if row["resource_id"] == source["id"]
        )

    broken = upload(b"# Only a heading", title="Synthetic private failure")
    index_once()
    failed = operation(broken)
    check(
        failed["status"] == "failed" and failed["can_retry"] and failed["attempts"] == 1,
        "Real parser failure appears with bounded recovery action",
    )
    trace = a.get(root + f"/activity/indexing/{failed['id']}").json()
    check(
        [e["phase"] for e in trace["timeline"]] == ["queued", "started", "failed"],
        "Worker transitions persist in correlated chronological timeline",
    )
    check(
        "Only a heading" not in str(trace) and "content_base64" not in str(trace),
        "Activity contains no uploaded source body or credential envelope",
    )
    check(
        b.get(root + "/activity").status_code == 404
        and b.get(root + f"/activity/indexing/{failed['id']}").status_code == 404,
        "Cross-workspace list and operation lookup denied",
    )
    sql("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u", w=wa, u=ua)
    check(
        activity(kind="indexing")["total"] == 0
        and a.get(root + f"/activity/indexing/{failed['id']}").status_code == 404,
        "Viewer cannot discover unpublished source operation metadata",
    )
    check(
        a.post(
            root + f"/activity/indexing/{failed['id']}/retry",
            json={"expected_revision": failed["revision"]},
        ).status_code
        == 403,
        "Viewer recovery denied server-side",
    )
    sql("UPDATE membership SET role='admin' WHERE workspace_id=:w AND user_id=:u", w=wa, u=ua)
    with ThreadPoolExecutor(2) as pool:
        replies = list(
            pool.map(
                lambda _: a.post(
                    root + f"/activity/indexing/{failed['id']}/retry",
                    json={"expected_revision": failed["revision"]},
                ),
                range(2),
            )
        )
    check(
        sorted(r.status_code for r in replies) == [200, 409],
        "Concurrent retry queues one recovery command",
    )
    index_once()
    second = operation(broken)
    check(
        second["attempts"] == 2 and second["status"] == "failed",
        "Failed retry preserves cumulative attempt count",
    )
    r = a.post(
        root + f"/activity/indexing/{second['id']}/retry",
        json={"expected_revision": second["revision"]},
    )
    r.raise_for_status()
    index_once()
    third = operation(broken)
    check(
        third["attempts"] == 3 and not third["can_retry"],
        "Three-attempt cap disables further recovery",
    )
    check(
        a.post(
            root + f"/activity/indexing/{third['id']}/retry",
            json={"expected_revision": third["revision"]},
        ).status_code
        == 409,
        "Attempt cap enforced through recovery API",
    )

    good = upload(
        b"# Project access\nChanging a workspace role from Admin to Member does not remove explicit project membership. A project Admin can invite a teammate to the project. Check membership before advising about access."
    )
    with engine.connect() as db:
        job_id = db.scalar(
            text("SELECT id FROM knowledge_job WHERE version_id=:v"), {"v": good["version_id"]}
        )
    # Seed the durable state left by an interrupted worker; execution below uses the real worker.
    sql(
        "UPDATE knowledge_job SET status='processing', attempts=1,lease_token=:token,lease_until=now()+interval '2 minutes' WHERE id=:j",
        token=uuid4(),
        j=job_id,
    )
    running = operation(good)
    check(
        not running["can_retry"]
        and a.post(
            root + f"/activity/indexing/{job_id}/retry",
            json={"expected_revision": running["revision"]},
        ).status_code
        == 409,
        "An active worker lease cannot be stolen by operator recovery",
    )
    sql("UPDATE knowledge_job SET lease_until=now()-interval '1 minute' WHERE id=:j", j=job_id)
    expired = operation(good)
    check(
        expired["lease_expired"] and expired["can_retry"],
        "Expired durable worker lease exposes recovery",
    )
    a.post(
        root + f"/activity/indexing/{job_id}/retry", json={"expected_revision": expired["revision"]}
    ).raise_for_status()
    index_once()
    ready = doc(good)
    check(
        ready["status"] == "ready" and ready["job"]["attempts"] == 2,
        "Restarted real worker safely finishes interrupted durable operation",
    )
    count = len(ready["sections"])
    index_once()
    check(
        len(doc(good)["sections"]) == count and count > 0,
        "Repeated worker start does not duplicate indexed effects",
    )
    published = a.post(
        root + f"/knowledge/{good['id']}/publish", json={"expected_revision": ready["revision"]}
    )
    published.raise_for_status()
    evidence = a.post(ticket + "/retrievals")
    evidence.raise_for_status()
    check(
        bool(evidence.json()["results"]),
        "Published synthetic source is retrievable before retirement",
    )
    d = a.get(ticket).json()
    queued = a.post(
        ticket + "/generations",
        json={
            "expected_revision": d["revision"],
            "retrieval_id": evidence.json()["id"],
            "request_id": str(uuid4()),
        },
    )
    queued.raise_for_status()
    generate_once()
    d = a.get(ticket).json()
    check(d["draft"]["citation_ids"], "Actual fixture worker saves a source-dependent draft")
    review = a.post(
        ticket + "/approval-reviews",
        json={
            "expected_revision": d["revision"],
            "draft_id": d["draft"]["id"],
            "status": d["status"],
            "priority": d["priority"],
            "assigned_to": d["assigned_to"],
        },
    )
    review.raise_for_status()
    citation = d["draft"]["citation_ids"][0]
    fresh_evidence = a.post(ticket + "/retrievals")
    fresh_evidence.raise_for_status()
    pending = a.post(
        ticket + "/generations",
        json={
            "expected_revision": d["revision"],
            "retrieval_id": fresh_evidence.json()["id"],
            "request_id": str(uuid4()),
        },
    )
    pending.raise_for_status()
    a.post(
        root + f"/knowledge/{good['id']}/archive",
        json={"expected_revision": published.json()["revision"]},
    ).raise_for_status()
    check(
        a.post(ticket + f"/approval-reviews/{review.json()['id']}/approve", json={}).status_code
        == 409,
        "Source archive invalidates exact reply approval",
    )
    check(
        a.get(root + f"/citations/{citation}").status_code == 404,
        "Archived source no longer opens through historical citation",
    )
    archived = doc(good)
    removed = a.post(
        root + f"/knowledge/{good['id']}/delete", json={"expected_revision": archived["revision"]}
    )
    removed.raise_for_status()
    check(
        removed.json()["status"] == "deleted" and removed.json()["title"] == "Deleted source",
        "Deletion retains a content-free source tombstone",
    )
    with engine.connect() as db:
        row = db.execute(
            text(
                "SELECT content,source_bytes,filename,content_hash FROM document_version WHERE id=:v"
            ),
            {"v": good["version_id"]},
        ).one()
        check(
            row.content == ""
            and row.source_bytes is None
            and row.filename == "deleted"
            and row.content_hash == "",
            "Deletion erases source text, file bytes, filename and content hash",
        )
        check(
            db.scalar(
                text("SELECT count(*) FROM knowledge_chunk WHERE version_id=:v"),
                {"v": good["version_id"]},
            )
            == 0,
            "Deletion erases indexed text and vectors",
        )
    check(
        a.get(root + f"/knowledge/{good['id']}/download").status_code == 404,
        "Even Admin cannot download a deleted source",
    )
    historical = a.get(ticket + "/retrievals/latest").json()
    check(
        historical["sources_changed"] and historical["results"] == [],
        "Deleted passages retain explicit stale evidence rather than ordinary empty evidence",
    )
    generate_once()
    failed_generation = a.get(ticket + "/generations/latest").json()
    check(
        failed_generation["id"] == pending.json()["id"]
        and failed_generation["status"] == "failed"
        and a.get(ticket).json()["draft"]["id"] == d["draft"]["id"],
        "Source deletion rejects queued generation before provider requests and preserves saved draft",
    )
    deleted_trace = a.get(root + f"/activity/indexing/{job_id}").json()
    check(
        deleted_trace["status"] == "deleted"
        and not deleted_trace["can_retry"]
        and any(e["phase"] == "delete" for e in deleted_trace["timeline"]),
        "Deletion and unavailable-source impact appear in operational history",
    )
    check(
        activity(state="deleted")["total"] == 1 and len(activity(limit=1)["items"]) == 1,
        "State filters and bounded pagination use real operation records",
    )
    check(
        a.post(
            root + f"/activity/generation/{queued.json()['id']}/retry",
            json={"expected_revision": d["revision"]},
        ).status_code
        == 404,
        "Activity provides no automatic provider retry path",
    )

    pdf = upload(
        (Path(__file__).parent / "fixtures/access-guide.pdf").read_bytes(),
        title="Synthetic PDF erasure",
        filename="access.pdf",
    )
    a.post(
        root + f"/knowledge/{pdf['id']}/delete", json={"expected_revision": pdf["revision"]}
    ).raise_for_status()
    with engine.connect() as db:
        check(
            db.scalar(
                text("SELECT source_bytes IS NULL FROM document_version WHERE id=:v"),
                {"v": pdf["version_id"]},
            ),
            "Deletion removes actual PDF bytes before indexing",
        )
    check(not index_once(), "Deleted queued sources cannot be revived by worker restart")
    print(
        f"\n{len(checks)} genuine HTTP/PostgreSQL/worker assertions passed; no paid AI or email requests."
    )
finally:
    with engine.begin() as db:
        for w in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": w})
        for u in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": u})
