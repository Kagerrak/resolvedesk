"""Post-implementation public HTTP + real PostgreSQL manual-handling scenarios."""

import os
from concurrent.futures import ThreadPoolExecutor

import httpx
from sqlalchemy import text

from resolvedesk.database import engine

WEB = os.environ.get("SCENARIO_WEB_URL", "http://localhost:3000")
checks, users, workspaces = [], [], []


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
    workspace = client.post("/api/backend/demo").json()["id"]
    workspaces.append(workspace)
    return client, user, workspace


try:
    a, ua, wa = visitor()
    b, ub, wb = visitor()
    queue = f"/api/backend/workspaces/{wa}/tickets"
    t = a.get(queue).json()[0]
    path = f"{queue}/{t['id']}"
    first = a.get(path).json()
    check(
        first["draft"] is None and first["events"] == [],
        "New ticket has no fabricated draft/history",
    )
    check(
        len(a.get(queue, params={"q": "ALEX", "status": "open"}).json()) == 1,
        "Proxy forwards case-insensitive persisted search and status filter",
    )
    check(
        a.get(queue, params={"q": "%"}).json() == [], "Search treats wildcard characters literally"
    )
    check(
        a.get(queue, params={"status": "resolved"}).json() == [],
        "Status filter selects real states",
    )
    check(a.get(queue, params={"q": "x" * 201}).status_code == 422, "Search length is bounded")
    check(
        b.get(f"/api/backend/workspaces/{wa}/members").status_code == 404,
        "Member list is workspace scoped",
    )
    check(
        b.post(path + "/draft", json={"expected_revision": 1, "body": "intrusion"}).status_code
        == 404,
        "Other workspace cannot save a draft",
    )
    fields = {
        "expected_revision": t["revision"],
        "status": "pending",
        "priority": "high",
        "assigned_to": ua,
    }
    foreign = a.patch(path, json={**fields, "assigned_to": ub})
    check(foreign.status_code == 422, "Foreign-workspace assignee rejected")
    result = a.patch(path, json=fields)
    result.raise_for_status()
    current = result.json()
    check(
        current["status"] == "pending"
        and current["priority"] == "high"
        and current["assigned_to"] == ua,
        "Explicit status, priority and assignment persist",
    )
    check(a.get(path).json() == current, "Ticket changes survive a separate HTTP read")
    check(
        len(a.get(queue, params={"assignment": "mine", "status": "pending"}).json()) == 1
        and a.get(queue, params={"assignment": "unassigned"}).json() == [],
        "Assignment filters use persisted membership",
    )
    check(
        len(current["events"]) == 1
        and set(current["events"][0]["changes"]) == {"status", "priority", "assigned_to"},
        "One atomic audit event captures exact field changes",
    )
    check(
        a.patch(path, json=fields).status_code == 409,
        "Stale ticket change cannot overwrite newer work",
    )
    fields["expected_revision"] = current["revision"]
    same = a.patch(path, json=fields).json()
    check(
        same["revision"] == current["revision"] and same["events"] == current["events"],
        "No-op ticket update does not create history",
    )
    draft_body = "Synthetic reply for review. No delivery is authorized."
    draft = a.post(
        path + "/draft", json={"expected_revision": current["revision"], "body": draft_body}
    )
    draft.raise_for_status()
    current = draft.json()
    check(
        current["draft"]["body"] == draft_body
        and len(current["messages"]) == len(first["messages"]),
        "Saved draft is a revision, never a delivered message",
    )
    check(a.get(path).json()["draft"] == current["draft"], "Draft survives independent reload")
    check(
        current["events"][-1]["action"] == "draft_saved"
        and "body" not in str(current["events"][-1]["changes"]),
        "Draft audit references revision without duplicating reply content",
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda body: a.post(
                    path + "/draft", json={"expected_revision": current["revision"], "body": body}
                ),
                ["Concurrent draft A", "Concurrent draft B"],
            )
        )
    check(
        sorted(r.status_code for r in responses) == [200, 409],
        "Concurrent writers: exactly one revision succeeds; other conflicts",
    )
    current = a.get(path).json()
    check(
        a.post(
            path + "/draft", json={"expected_revision": current["revision"], "body": "x" * 20001}
        ).status_code
        == 422,
        "Oversized draft is rejected",
    )
    check(
        a.post(
            path + "/draft",
            headers={"Origin": "https://untrusted.example"},
            json={"expected_revision": current["revision"], "body": "bad"},
        ).status_code
        == 403,
        "Cross-origin draft mutation rejected",
    )
    current = a.patch(
        path, json={**fields, "expected_revision": current["revision"], "status": "resolved"}
    ).json()
    check(current["status"] == "resolved", "Explicit resolve persists")
    check(
        a.patch(
            path, json={**fields, "expected_revision": current["revision"], "status": "open"}
        ).status_code
        == 422,
        "Resolved ticket cannot reopen implicitly",
    )
    current = a.patch(
        path,
        json={**fields, "expected_revision": current["revision"], "status": "open", "reopen": True},
    ).json()
    check(
        current["status"] == "open" and current["events"][-1]["action"] == "ticket_reopened",
        "Explicit reopen persists and is audited",
    )
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    check(a.get(path).status_code == 200, "Viewer can inspect saved draft and history")
    check(
        a.post(
            path + "/draft", json={"expected_revision": current["revision"], "body": "unauthorized"}
        ).status_code
        == 403,
        "Viewer cannot save draft",
    )
    check(
        a.patch(path, json={**fields, "expected_revision": current["revision"]}).status_code == 403,
        "Viewer cannot change ticket",
    )
    check(
        a.get(path).json() == current, "Rejected Viewer mutations change neither ticket nor audit"
    )
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='agent' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    current = a.post(
        path + "/draft", json={"expected_revision": current["revision"], "body": ""}
    ).json()
    check(
        current["draft"]["body"] == "", "Explicitly clearing a draft creates a saved empty revision"
    )
    with engine.connect() as db:
        count = db.scalar(
            text("SELECT count(*) FROM draft_revision WHERE ticket_id=:t"), {"t": t["id"]}
        )
        messages = db.scalar(
            text("SELECT count(*) FROM message WHERE ticket_id=:t"), {"t": t["id"]}
        )
    check(
        count == 3 and messages == 1,
        "Database retains three real revisions and only the original message",
    )
    print(f"\n{len(checks)} assertions passed. Real HTTP, Better Auth and PostgreSQL; no mocks.")
finally:
    with engine.begin() as db:
        for workspace in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": workspace})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
