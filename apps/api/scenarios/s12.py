"""Implementation-first HTTP/PostgreSQL verification of the public fixture deployment profile."""

import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text

from resolvedesk.database import SessionLocal, engine
from resolvedesk.generation import Generate, queue
from resolvedesk.identity import Identity
from resolvedesk.local_admin import grant

WEB, API = "http://localhost:3000", "http://localhost:8001"
SECRET = "resolvedesk-s12-maintenance-fixture-only"
users, workspaces, checks = [], [], []
process = None
log = None
window_hour, saved_window = None, None
request_count, request_lock = 0, Lock()


def pace(_):
    global request_count
    with request_lock:
        request_count += 1
        quiet = request_count % 40 == 0
    if quiet:
        print("Waiting for the real sign-in quiet window; guard remains enabled.", flush=True)
        time.sleep(30.5)
        time.sleep(30.5)
    else:
        time.sleep(1.3)


def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label, flush=True)


def scalar(statement, **values):
    with engine.connect() as db:
        return db.scalar(text(statement), values)


def sql(statement, **values):
    with engine.begin() as db:
        return db.execute(text(statement), values)


def visitor():
    client = httpx.Client(headers={"Origin": WEB}, timeout=30, event_hooks={"response": [pace]})
    r = client.post(WEB + "/api/auth/sign-in/anonymous", json={})
    r.raise_for_status()
    user = r.json()["user"]["id"]
    users.append(user)
    return client, user


def demo(client):
    r = client.post(API + "/demo")
    r.raise_for_status()
    value = r.json()
    workspaces.append(value["id"])
    return value


try:
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8001)) == 0:
            raise RuntimeError("Port8001 is already occupied; preserve that process.")
    env = dict(os.environ, PUBLIC_DEMO_ONLY="true", LIVE_AI_ENABLED="false", CRON_SECRET=SECRET)
    with open("/tmp/resolvedesk-s12-api.log", "w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "resolvedesk.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8001",
            ],
            env=env,
            stdout=log,
            stderr=log,
        )
    for _ in range(40):
        try:
            if httpx.get(API + "/health").status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    else:
        raise RuntimeError("Public profile did not start; inspect the local server log.")
    before_cost = scalar("SELECT coalesce(sum(allocated_micros),0) FROM usage_month")
    a, ua = visitor()
    b, ub = visitor()
    wa = demo(a)
    wb = demo(b)
    root = API + f"/workspaces/{wa['id']}"
    other = API + f"/workspaces/{wb['id']}"
    check(
        wa["public_demo"] and wb["public_demo"] and wa["role"] == "agent" and wa["id"] != wb["id"],
        "Two real authenticated visitors receive distinct tagged Agent workspaces",
    )
    check(demo(a)["id"] == wa["id"], "Repeated entry preserves the same public workspace")
    check(
        httpx.get(API + "/public-policy").json()["generation_mode"] == "fixture",
        "Public policy reports fixture mode without provider activation",
    )
    ta = a.get(root + "/tickets").json()
    tb = b.get(other + "/tickets").json()
    check(
        len(ta) == 3 and len(tb) == 3 and ta[0]["number"] == 1042,
        "Approved synthetic role billing and stale-source conversations are persisted",
    )
    response_a, response_b = a.get(root + "/knowledge"), b.get(other + "/knowledge")
    response_a.raise_for_status()
    response_b.raise_for_status()
    docs_a, docs_b = response_a.json(), response_b.json()
    check(
        len(docs_a) == 4
        and all(d["status"] == "published" for d in docs_a)
        and not ({d["id"] for d in docs_a} & {d["id"] for d in docs_b}),
        "Identical approved content has separate published source identities per visitor",
    )
    check(
        b.get(root + "/tickets").status_code == 404
        and b.get(root + f"/knowledge/{docs_a[0]['id']}").status_code == 404,
        "Foreign visitor cannot read ticket or source details",
    )
    check(
        a.post(
            root + "/knowledge",
            json={"title": "Forbidden", "filename": "x.txt", "content_base64": "eA=="},
        ).status_code
        == 403
        and a.post(root + "/evaluations", json={"request_id": str(uuid4())}).status_code == 403,
        "Public visitors cannot upload or start Admin evaluation jobs",
    )
    try:
        grant(UUID(wa["id"]))
    except SystemExit:
        check(True, "Local Admin setup refuses an explicitly public workspace")
    else:
        raise AssertionError("Public Admin grant was accepted")
    primary = root + f"/tickets/{ta[0]['id']}"
    evidence = a.post(primary + "/retrievals")
    evidence.raise_for_status()
    ea = evidence.json()
    check(
        ea["results"]
        and not (
            {str(r["version_id"]) for r in ea["results"]} & {str(d["version_id"]) for d in docs_b}
        ),
        "Actual pgvector results exclude the other visitor's deliberately identical sources",
    )
    check(
        b.get(root + f"/citations/{ea['results'][0]['id']}").status_code == 404,
        "Citation navigation remains scoped to its visitor workspace",
    )
    payload = {
        "expected_revision": ta[0]["revision"],
        "retrieval_id": ea["id"],
        "request_id": str(uuid4()),
    }
    check(
        a.post(primary + "/generations", json={**payload, "mode": "deepseek"}).status_code == 422,
        "Paid provider mode is not an accepted public request field",
    )
    generated = a.post(primary + "/generations", json=payload)
    generated.raise_for_status()
    check(
        generated.json()["status"] == "succeeded"
        and generated.json()["request_id"] == payload["request_id"],
        "Public request runs the real targeted fixture worker and identifies the saved intent",
    )
    detail = a.get(primary).json()
    check(
        detail["draft"]["citation_ids"] and len(detail["messages"]) == 1,
        "Generated revision has evidence and does not deliver a reply",
    )
    review = a.post(
        primary + "/approval-reviews",
        json={
            "expected_revision": detail["revision"],
            "draft_id": detail["draft"]["id"],
            "status": detail["status"],
            "priority": detail["priority"],
            "assigned_to": None,
        },
    )
    review.raise_for_status()
    approved = a.post(primary + f"/approval-reviews/{review.json()['id']}/approve", json={})
    approved.raise_for_status()
    check(
        len(approved.json()["messages"]) == 2
        and approved.json()["messages"][-1]["kind"] == "simulated_reply",
        "Only exact explicit approval records a synthetic reply; no mail transport is used",
    )
    again = a.post(primary + f"/approval-reviews/{review.json()['id']}/approve", json={})
    check(
        again.status_code == 200 and len(again.json()["messages"]) == 2,
        "Repeated approval preserves one simulated receipt/message",
    )
    # A real committed queue checkpoint, intentionally left before dispatch, models an interrupted request.
    bd = b.get(other + f"/tickets/{tb[0]['id']}").json()
    be = b.post(other + f"/tickets/{tb[0]['id']}/retrievals").json()
    with SessionLocal() as db:
        pending = queue(
            db,
            UUID(wb["id"]),
            UUID(tb[0]["id"]),
            Generate(
                expected_revision=bd["revision"], retrieval_id=UUID(be["id"]), request_id=uuid4()
            ),
            Identity(ub, True),
        )
        pending_id = pending.id
        db.commit()
    resumed = b.post(other + f"/tickets/{tb[0]['id']}/generations/{pending_id}/resume")
    check(
        resumed.status_code == 200 and resumed.json()["status"] == "succeeded",
        "Explicit public resume consumes an actual durable fixture checkpoint without a new job",
    )
    check(
        scalar("SELECT count(*) FROM generation_run WHERE workspace_id=:w", w=wb["id"]) == 1,
        "Resuming a saved intent does not consume another generation slot",
    )
    # Eight more genuine request-driven generations bring A to nine, before distinct-ticket concurrency.
    for _ in range(8):
        d = a.get(primary).json()
        e = a.post(primary + "/retrievals").json()
        a.post(
            primary + "/generations",
            json={
                "expected_revision": d["revision"],
                "retrieval_id": e["id"],
                "request_id": str(uuid4()),
            },
        ).raise_for_status()
    final_payloads = []
    for ticket in ta[1:]:
        route = root + f"/tickets/{ticket['id']}"
        e = a.post(route + "/retrievals").json()
        final_payloads.append(
            (
                route,
                {
                    "expected_revision": ticket["revision"],
                    "retrieval_id": e["id"],
                    "request_id": str(uuid4()),
                },
            )
        )
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(lambda pair: a.post(pair[0] + "/generations", json=pair[1]), final_payloads)
        )
    check(
        sorted(r.status_code for r in results) == [202, 429]
        and scalar("SELECT count(*) FROM generation_run WHERE workspace_id=:w", w=wa["id"]) == 10,
        "Concurrent public tickets cannot exceed the ten-generation session quota",
    )
    sql("UPDATE demo_quota SET retrievals=29 WHERE workspace_id=:w", w=wa["id"])
    with ThreadPoolExecutor(2) as pool:
        searches = list(pool.map(lambda t: a.post(root + f"/tickets/{t['id']}/retrievals"), ta[1:]))
    check(
        sorted(r.status_code for r in searches) == [201, 429]
        and scalar("SELECT retrievals FROM demo_quota WHERE workspace_id=:w", w=wa["id"]) == 30,
        "Actual PostgreSQL search reservations enforce the last shared slot atomically",
    )
    sql("UPDATE demo_quota SET writes=99 WHERE workspace_id=:w", w=wa["id"])
    edits = []
    for t in ta[1:]:
        route = root + f"/tickets/{t['id']}"
        d = a.get(route).json()
        edits.append(
            (route, {"expected_revision": d["revision"], "body": "Synthetic manual review draft."})
        )
    with ThreadPoolExecutor(2) as pool:
        saves = list(pool.map(lambda pair: a.post(pair[0] + "/draft", json=pair[1]), edits))
    check(
        sorted(r.status_code for r in saves) == [200, 429]
        and scalar("SELECT writes FROM demo_quota WHERE workspace_id=:w", w=wa["id"]) == 100,
        "Saved-action quota is shared and atomic across distinct conversations",
    )
    check(
        a.get(primary).status_code == 200
        and a.get(root + "/activity").status_code == 200
        and a.get(root + f"/citations/{ea['results'][0]['id']}").status_code == 200,
        "Exhausted limits preserve conversation evidence and history exploration",
    )
    # Real extra memberships cannot open a live/local context through the public profile.
    legacy = str(uuid4())
    workspaces.append(legacy)
    sql(
        "INSERT INTO workspace(id,name,public_demo) VALUES(:w,'Preserved synthetic local context',false)",
        w=legacy,
    )
    sql("INSERT INTO membership(workspace_id,user_id,role) VALUES(:w,:u,'admin')", w=legacy, u=ua)
    check(
        a.get(API + f"/workspaces/{legacy}/knowledge").status_code == 404
        and a.post(
            API + f"/workspaces/{legacy}/knowledge",
            json={"title": "No", "filename": "x.txt", "content_base64": "eA=="},
        ).status_code
        == 404,
        "Public deployment cannot read or manage a nonpublic context even with accidental membership",
    )
    sql("DELETE FROM membership WHERE workspace_id=:w", w=legacy)
    c, uc = visitor()
    if datetime.now(UTC).minute == 59 and datetime.now(UTC).second >= 58:
        time.sleep(2)
    window_hour = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    sql("INSERT INTO demo_window(hour,sessions) VALUES(:h,0) ON CONFLICT DO NOTHING", h=window_hour)
    saved_window = scalar("SELECT sessions FROM demo_window WHERE hour=:h", h=window_hour)
    sql("UPDATE demo_window SET sessions=20 WHERE hour=:h", h=window_hour)
    check(
        c.post(API + "/demo").status_code == 429
        and scalar("SELECT count(*) FROM workspace WHERE demo_owner=:u", u=uc) == 0,
        "Global hourly creation allowance rejects excess sessions before seeding content",
    )
    sql("UPDATE demo_window SET sessions=:n WHERE hour=:h", n=saved_window, h=window_hour)
    saved_window = None
    sql("UPDATE workspace SET expires_at=now()-interval '1 second' WHERE id=:w", w=wa["id"])
    check(a.get(primary).status_code == 404, "Expiry immediately revokes public data access")
    check(
        httpx.post(API + "/internal/maintenance", headers={"Origin": WEB}).status_code == 401,
        "Cleanup requires the server-only maintenance credential",
    )
    cleaned = httpx.post(
        API + "/internal/maintenance", headers={"Origin": WEB, "Authorization": "Bearer " + SECRET}
    ).json()
    check(
        cleaned["deleted_workspaces"] >= 1
        and scalar("SELECT count(*) FROM workspace WHERE id=:w", w=wa["id"]) == 0
        and scalar("SELECT count(*) FROM knowledge_chunk WHERE workspace_id=:w", w=wa["id"]) == 0
        and scalar("SELECT count(*) FROM draft_revision WHERE workspace_id=:w", w=wa["id"]) == 0,
        "Actual expiry cleanup removes public sources vectors drafts jobs and handling content",
    )
    check(
        scalar("SELECT count(*) FROM workspace WHERE id=:w", w=legacy) == 1
        and scalar("SELECT coalesce(sum(allocated_micros),0) FROM usage_month") == before_cost,
        "Cleanup preserves untagged local work and the global monthly spending ledger",
    )
    check(
        b.get(other + "/tickets").status_code == 200,
        "Cleaning one visitor preserves another active visitor",
    )
    invalid = subprocess.run(
        [sys.executable, "-c", "import resolvedesk.config"],
        env={**env, "LIVE_AI_ENABLED": "true"},
        check=False,
        capture_output=True,
        text=True,
    )
    check(
        invalid.returncode != 0 and "Public demo deployment requires" in invalid.stderr,
        "Public deployment refuses to start with paid provider dispatch enabled",
    )
    check(
        scalar(
            "SELECT count(*) FROM generation_run WHERE workspace_id=:w AND mode <> 'fixture'",
            w=wb["id"],
        )
        == 0,
        "All public generation verification remains fixture-only with zero paid requests",
    )
    print(f"\n{len(checks)} genuine public HTTP/PostgreSQL/profile assertions passed.")
finally:
    if saved_window is not None:
        sql("UPDATE demo_window SET sessions=:n WHERE hour=:h", n=saved_window, h=window_hour)
    with engine.begin() as db:
        for w in set(workspaces):
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": w})
        for u in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": u})
    if process:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
