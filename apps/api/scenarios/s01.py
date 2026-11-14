"""Post-implementation HTTP/PostgreSQL scenarios. Run only against a disposable local database."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from resolvedesk.database import engine

WEB = os.environ.get("SCENARIO_WEB_URL", "http://localhost:3000")
API = os.environ.get("SCENARIO_API_URL", "http://127.0.0.1:8000")
users = []
workspaces = []
checks = []


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


def visitor():
    client = httpx.Client(base_url=WEB, headers={"Origin": WEB}, timeout=20)
    response = client.post("/api/auth/sign-in/anonymous", json={})
    check(response.status_code == 200, "Maintained auth creates anonymous session")
    users.append(response.json()["user"]["id"])
    return client


try:
    a, b = visitor(), visitor()
    wa = a.post("/api/backend/demo").json()
    wb = b.post("/api/backend/demo").json()
    workspaces.extend([wa["id"], wb["id"]])
    check(wa["id"] != wb["id"], "Two sessions receive distinct persisted workspaces")
    ta = a.get(f"/api/backend/workspaces/{wa['id']}/tickets").json()[0]
    tb = b.get(f"/api/backend/workspaces/{wb['id']}/tickets").json()[0]
    detail_path = f"/api/backend/workspaces/{wa['id']}/tickets/{ta['id']}"
    detail = a.get(detail_path).json()
    check(len(detail["messages"]) == 1, "Persisted ticket includes its stored message")
    check(
        a.get(detail_path).json() == detail,
        "Reload preserves ticket and message identities/content",
    )
    check(b.get(detail_path).status_code == 404, "Other session cannot read workspace ticket")
    check(
        a.get(f"/api/backend/workspaces/{wa['id']}/tickets/{tb['id']}").status_code == 404,
        "Mixed workspace/ticket identifiers reveal nothing",
    )
    check(
        a.get("/api/backend/workspaces").json()[0]["id"] == wa["id"],
        "Workspace list only returns authorized membership",
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda _: a.post("/api/backend/demo").json()["id"], range(4)))
    check(set(rows) == {wa["id"]}, "Concurrent demo retries reuse one workspace")
    with engine.begin() as db:
        count = db.scalar(
            text("SELECT count(*) FROM ticket WHERE workspace_id = :w"), {"w": wa["id"]}
        )
        check(count == 1, "Concurrent retries do not duplicate the sample ticket")
    check(
        httpx.get(
            API + "/workspaces", headers={"X-User-ID": users[0], "X-Role": "admin"}
        ).status_code
        == 401,
        "Forged identity headers are rejected",
    )
    check(
        a.post("/api/backend/demo", headers={"Origin": "https://untrusted.example"}).status_code
        == 403,
        "Web rejects cross-origin mutations",
    )
    check(
        httpx.post(
            API + "/demo", cookies=a.cookies, headers={"Origin": "https://untrusted.example"}
        ).status_code
        == 403,
        "API independently rejects cross-origin mutations",
    )
    with engine.begin() as db:
        db.execute(text("UPDATE membership SET role='viewer' WHERE user_id=:u"), {"u": users[0]})
    check(
        a.get("/api/backend/workspaces").json()[0]["role"] == "viewer",
        "Role changes take effect without a new session",
    )
    check(a.get(detail_path).status_code == 200, "Viewer can inspect persisted ticket")
    check(a.post(detail_path).status_code == 405, "Read-only S01 API exposes no ticket mutation")
    with engine.begin() as db:
        db.execute(text("DELETE FROM membership WHERE user_id=:u"), {"u": users[0]})
    check(
        a.get(detail_path).status_code == 404, "Revoked membership immediately denies ticket access"
    )
    try:
        with engine.begin() as db:
            db.execute(
                text(
                    "INSERT INTO message(id, workspace_id, ticket_id, sender_name, sender_email, body, created_at) VALUES (:id,:w,:t,'Synthetic','synthetic@example.com','Invalid ownership',now())"
                ),
                {"id": str(uuid4()), "w": wa["id"], "t": tb["id"]},
            )
    except IntegrityError as error:
        check(
            isinstance(error, IntegrityError),
            "Database rejects mismatched message/ticket workspace",
        )
    else:
        raise AssertionError("Ownership constraint accepted invalid message")
    with engine.begin() as db:
        db.execute(
            text('UPDATE "session" SET "expiresAt"=now()-interval \'1 minute\' WHERE "userId"=:u'),
            {"u": users[1]},
        )
    check(
        b.get("/api/backend/workspaces").status_code == 401,
        "Expired Better Auth session is rejected",
    )
    check(
        a.post("/api/auth/sign-out", json={}).status_code == 200, "Session can be explicitly ended"
    )
    check(a.get("/api/backend/workspaces").status_code == 401, "Ended session cannot read inbox")
    print(
        f"\n{len(checks)} scenario assertions passed. Real HTTP, Better Auth and PostgreSQL; no mocks."
    )
finally:
    with engine.begin() as db:
        for workspace in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": workspace})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
