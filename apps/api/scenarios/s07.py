"""Post-implementation genuine HTTP/PostgreSQL approval scenarios; no email/provider calls."""

import base64
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.knowledge_worker import run_once as index_once
from resolvedesk.local_admin import grant

WEB = "http://localhost:3000"
users, workspaces, checks = [], [], []


def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


def visitor():
    client = httpx.Client(
        base_url=WEB,
        headers={"Origin": WEB},
        timeout=30,
        event_hooks={"response": [lambda _: time.sleep(1.1)]},
    )
    r = client.post("/api/auth/sign-in/anonymous", json={})
    r.raise_for_status()
    user = r.json()["user"]["id"]
    users.append(user)
    r = client.post("/api/backend/demo")
    r.raise_for_status()
    w = r.json()["id"]
    workspaces.append(w)
    t = client.get(f"/api/backend/workspaces/{w}/tickets").json()[0]["id"]
    return client, user, w, t


try:
    a, ua, wa, ta = visitor()
    b, ub, wb, tb = visitor()
    path = f"/api/backend/workspaces/{wa}/tickets/{ta}"

    def detail():
        r = a.get(path)
        r.raise_for_status()
        return r.json()

    def save(body):
        r = a.post(path + "/draft", json={"expected_revision": detail()["revision"], "body": body})
        r.raise_for_status()
        return r.json()

    def review(**values):
        d = detail()
        return a.post(
            path + "/approval-reviews",
            json={
                "expected_revision": d["revision"],
                "draft_id": d["draft"]["id"],
                "status": d["status"],
                "priority": d["priority"],
                "assigned_to": d["assigned_to"],
                "tags": d["tags"],
                **values,
            },
        )

    def approve(r, client=a, **values):
        return client.post(
            path + f"/approval-reviews/{r['id']}/approve",
            json={"acknowledge_unverified": True, **values},
        )

    def sql(statement, **values):
        with engine.begin() as db:
            return db.execute(text(statement), values)

    save("Synthetic reviewed reply. No account action has been performed.")
    r = review(priority="high", tags=[" Follow-up ", "follow-up"])
    r.raise_for_status()
    first = r.json()
    check(
        first["body"] == detail()["draft"]["body"] and first["warnings"],
        "Exact saved wording and absent-citation warning persisted",
    )
    check(
        first["actions"]["tags"]["after"] == ["follow-up"],
        "Tags normalized in exact proposed actions",
    )
    check(
        len(detail()["messages"]) == 1 and detail()["priority"] != "high",
        "Review alone changes no message or ticket fields",
    )
    check(
        approve(first, acknowledge_unverified=False).status_code == 422,
        "Uncited reply requires acknowledgement",
    )
    check(approve(first, client=b).status_code == 404, "Cross-workspace approval denied")
    sql("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u", w=wa, u=ua)
    check(
        approve(first).status_code == 403 and review().status_code == 403,
        "Viewer cannot prepare or approve replies",
    )
    sql("UPDATE membership SET role='agent' WHERE workspace_id=:w AND user_id=:u", w=wa, u=ua)
    save("Synthetic edited reply for renewed review.")
    check(approve(first).status_code == 409, "Editing invalidates prior review")
    current = review(priority="high", tags=["follow-up"]).json()
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: approve(current), range(2)))
    check(
        all(r.status_code == 200 for r in results),
        "Concurrent duplicate approvals return successful receipt",
    )
    delivered = detail()
    check(
        len(delivered["messages"]) == 2 and delivered["messages"][-1]["kind"] == "simulated_reply",
        "Exactly one synthetic message recorded",
    )
    check(
        delivered["messages"][-1]["body"] == current["body"]
        and delivered["priority"] == "high"
        and delivered["tags"] == ["follow-up"],
        "Approved wording and field changes commit together",
    )
    with engine.connect() as db:
        row = db.execute(
            text("SELECT content,message_id FROM approval_record WHERE review_id=:r"),
            {"r": current["id"]},
        ).one()
        check(
            row.content["body"] == current["body"] and row.message_id is not None,
            "Durable approval binds content/actions/basis to simulated message",
        )
        check(
            db.scalar(
                text("SELECT count(*) FROM approval_record WHERE draft_id=:d"),
                {"d": delivered["draft"]["id"]},
            )
            == 1,
            "Database records one intent per draft revision",
        )
    check(review().status_code == 409, "Same draft cannot be delivered through another review")
    check(
        approve(current).status_code == 200 and len(detail()["messages"]) == 2,
        "Lost-response replay reuses prior delivery",
    )
    save("Synthetic next reply.")
    r = review().json()
    sql(
        "INSERT INTO message (id,workspace_id,ticket_id,sender_name,sender_email,body,created_at) VALUES (:i,:w,:t,'Synthetic customer','customer@example.com','New information',now())",
        i=uuid4(),
        w=wa,
        t=ta,
    )
    check(
        approve(r).status_code == 409,
        "New conversation invalidates approval without revision increment",
    )
    r = review().json()
    d = detail()
    patch = a.patch(
        path,
        json={
            "expected_revision": d["revision"],
            "status": d["status"],
            "priority": "urgent",
            "assigned_to": None,
        },
    )
    patch.raise_for_status()
    check(approve(r).status_code == 409, "Ticket change invalidates reply review")
    with engine.connect() as db:
        check(
            db.scalar(
                text(
                    "SELECT count(*) FROM approval_record WHERE ticket_id=:t AND review_id IS NULL"
                ),
                {"t": ta},
            )
            == 1,
            "Explicit ticket command persists human authorization",
        )
    grant(wa)
    r = review().json()
    upload = a.post(
        f"/api/backend/workspaces/{wa}/knowledge",
        json={
            "title": "Synthetic support policy",
            "filename": "policy.txt",
            "content_base64": base64.b64encode(
                b"Synthetic support policy: verify the invoice in billing settings."
            ).decode(),
        },
    )
    upload.raise_for_status()
    doc = upload.json()
    index_once()
    doc = a.get(f"/api/backend/workspaces/{wa}/knowledge/{doc['id']}").json()
    pub = a.post(
        f"/api/backend/workspaces/{wa}/knowledge/{doc['id']}/publish",
        json={"expected_revision": doc["revision"]},
    )
    pub.raise_for_status()
    check(approve(r).status_code == 409, "New published source invalidates snapshot")
    r = review().json()
    archive = a.post(
        f"/api/backend/workspaces/{wa}/knowledge/{doc['id']}/archive",
        json={"expected_revision": pub.json()["revision"]},
    )
    archive.raise_for_status()
    check(approve(r).status_code == 409, "Source retirement invalidates review")
    valid = review().json()
    sql("UPDATE workspace SET demo_owner=NULL WHERE id=:w", w=wa)
    check(approve(valid).status_code == 403, "Simulated delivery refuses live workspaces")
    sql(
        "UPDATE workspace SET demo_owner=:u,expires_at=now()-interval '1 minute' WHERE id=:w",
        u=ua,
        w=wa,
    )
    check(approve(valid).status_code == 404, "Expired workspace cannot approve")
    print(f"\n{len(checks)} genuine HTTP/PostgreSQL assertions passed; no provider or email calls.")
finally:
    with engine.begin() as db:
        for w in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": w})
        for u in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": u})
