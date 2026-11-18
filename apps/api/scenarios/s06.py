"""Post-implementation real HTTP/PostgreSQL fixture-generation lifecycle and allowance checks."""

import base64
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text

from resolvedesk.config import settings
from resolvedesk.database import SessionLocal, engine
from resolvedesk.generation import (
    REQUEST_CAP,
    SESSION_CAP,
    context_for,
    reconcile,
    reserve,
    run_once,
)
from resolvedesk.knowledge_worker import run_once as index_once
from resolvedesk.local_admin import grant
from resolvedesk.models import GenerationRun, UsageMonth

WEB = "http://localhost:3000"
users, workspaces, checks = [], [], []


def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


def visitor():
    client = httpx.Client(base_url=WEB, headers={"Origin": WEB}, timeout=30)
    result = client.post("/api/auth/sign-in/anonymous", json={})
    result.raise_for_status()
    user = result.json()["user"]["id"]
    users.append(user)
    result = client.post("/api/backend/demo")
    result.raise_for_status()
    workspace = result.json()["id"]
    workspaces.append(workspace)
    ticket = client.get(f"/api/backend/workspaces/{workspace}/tickets").json()[0]["id"]
    return client, user, workspace, ticket


try:
    a, ua, wa, ta = visitor()
    b, ub, wb, tb = visitor()
    path = f"/api/backend/workspaces/{wa}/tickets/{ta}"
    foreign = f"/api/backend/workspaces/{wb}/tickets/{tb}"

    def detail():
        r = a.get(path)
        r.raise_for_status()
        return r.json()

    def retrieve():
        r = a.post(path + "/retrievals")
        r.raise_for_status()
        return r.json()

    def generate(evidence, revision=None, request=None):
        return a.post(
            path + "/generations",
            json={
                "expected_revision": revision or detail()["revision"],
                "retrieval_id": evidence["id"],
                "request_id": request or str(uuid4()),
            },
        )

    evidence = retrieve()
    request = str(uuid4())
    r = generate(evidence, request=request)
    r.raise_for_status()
    queued = r.json()
    check(
        queued["mode"] == "fixture" and queued["status"] == "queued",
        "Public generation queues explicit fixture mode",
    )
    check(
        generate(evidence, request=request).json()["id"] == queued["id"],
        "Retry request reuses persisted queued generation",
    )
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _: run_once(), range(2)))
    saved = detail()
    run = a.get(path + "/generations/latest").json()
    check(
        run["status"] == "escalated" and saved["draft"]["generation_id"] == run["id"],
        "Empty evidence creates persisted escalation draft",
    )
    check(
        len(saved["messages"]) == 1 and saved["draft"]["citation_ids"] == [],
        "Escalation is a draft, never an email or invented citation",
    )
    with engine.connect() as db:
        check(
            db.scalar(text("SELECT count(*) FROM draft_revision WHERE ticket_id=:t"), {"t": ta})
            == 1,
            "Concurrent workers create one draft revision",
        )
    evidence = retrieve()
    r = generate(evidence)
    r.raise_for_status()
    cancelled = r.json()
    check(
        a.post(path + f"/generations/{cancelled['id']}/cancel").json()["status"] == "cancelled",
        "Queued generation can be cancelled",
    )
    run_once()
    check(
        detail()["draft"]["id"] == saved["draft"]["id"], "Cancellation preserves prior saved draft"
    )
    grant(UUID(wa))
    route = f"/api/backend/workspaces/{wa}/knowledge"
    r = a.post(
        route,
        json={
            "title": "Synthetic project access",
            "filename": "access.md",
            "content_base64": base64.b64encode(
                b"# Project access\nProject membership is separate from workspace role. Ask a project Admin to inspect membership."
            ).decode(),
        },
    )
    r.raise_for_status()
    doc = r.json()
    index_once()
    doc = a.get(route + "/" + doc["id"]).json()
    r = a.post(route + "/" + doc["id"] + "/publish", json={"expected_revision": doc["revision"]})
    r.raise_for_status()
    doc = r.json()
    evidence = retrieve()
    r = generate(evidence)
    r.raise_for_status()
    run_once()
    saved = detail()
    run = a.get(path + "/generations/latest").json()
    check(
        run["status"] == "succeeded" and run["mode"] == "fixture",
        "Published evidence produces fixture extract draft",
    )
    check(
        set(saved["draft"]["citation_ids"]) <= {row["id"] for row in evidence["results"]}
        and saved["draft"]["citation_ids"],
        "Generated citations belong only to selected retrieval",
    )
    check(
        "Project membership" in saved["draft"]["body"] and len(saved["messages"]) == 1,
        "Generated draft contains actual source text without sending",
    )
    original_generation = saved["draft"]["generation_id"]
    r = a.post(
        path + "/draft",
        json={
            "expected_revision": saved["revision"],
            "body": saved["draft"]["body"] + "\nEdited by the Agent.",
        },
    )
    r.raise_for_status()
    edited = r.json()
    check(
        edited["draft"]["id"] != saved["draft"]["id"]
        and edited["draft"]["generation_id"] == original_generation
        and edited["draft"]["citation_ids"] == saved["draft"]["citation_ids"],
        "Human edit creates revision retaining generation provenance and citation references",
    )
    evidence = retrieve()
    r = generate(evidence)
    r.raise_for_status()
    stale = r.json()
    r = a.post(
        path + "/draft",
        json={"expected_revision": edited["revision"], "body": "Newer human draft."},
    )
    r.raise_for_status()
    newer = r.json()
    run_once()
    check(
        a.get(path + "/generations/latest").json()["status"] == "failed"
        and detail()["draft"]["id"] == newer["draft"]["id"],
        "Ticket revision change discards stale generation without overwriting newer draft",
    )
    check(
        b.get(path + "/generations/latest").status_code == 404,
        "Foreign workspace cannot inspect generation metadata",
    )
    check(
        a.post(
            foreign + "/generations",
            json={
                "expected_revision": 1,
                "retrieval_id": evidence["id"],
                "request_id": str(uuid4()),
            },
        ).status_code
        == 404,
        "Foreign workspace cannot queue generation",
    )
    evidence = retrieve()
    r = generate(evidence)
    r.raise_for_status()
    archive_run = r.json()
    a.post(
        route + "/" + doc["id"] + "/archive", json={"expected_revision": doc["revision"]}
    ).raise_for_status()
    run_once()
    check(
        a.get(path + "/generations/latest").json()["status"] == "failed"
        and detail()["draft"]["id"] == newer["draft"]["id"],
        "Source retirement before generation preserves saved draft",
    )
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    check(
        generate(evidence, revision=newer["revision"]).status_code == 403,
        "Viewer cannot generate draft",
    )
    check(
        a.post(path + f"/generations/{archive_run['id']}/cancel").status_code == 403,
        "Viewer cannot cancel generation",
    )
    check(
        a.get(path + "/generations/latest").status_code == 200,
        "Viewer can inspect generation outcome",
    )
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='admin' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    # Real transactional allowance operations on a fresh HTTP-created run and its scoped context.
    evidence = retrieve()
    response = generate(evidence)
    response.raise_for_status()
    budget_run = response.json()
    with SessionLocal() as db:
        gen = db.get(GenerationRun, UUID(budget_run["id"]))
        item, context = context_for(db, gen)
        reserve(db, gen, context)
        db.flush()
        month = gen.usage["month"]
        amount = gen.charge_micros
        ledger = db.get(UsageMonth, month)
        check(
            0 < amount <= REQUEST_CAP and ledger.allocated_micros >= amount,
            "Atomic ledger reserves bounded request allowance in PostgreSQL",
        )
        reconcile(db, gen, {"input_tokens": 100, "output_tokens": 20})
        db.flush()
        check(
            gen.charge_micros == 140 and gen.usage["accounted_micros"] == 140,
            "Measured usage releases unused conservative reservation",
        )
        ledger.allocated_micros = 20_000_000
        db.flush()
        rejected = False
        try:
            reserve(db, gen, context)
        except ValueError:
            rejected = True
        check(rejected, "Monthly ceiling denies a new reservation")
        db.rollback()
    with SessionLocal() as db:
        gen = db.get(GenerationRun, UUID(budget_run["id"]))
        gen.charge_micros = SESSION_CAP
        db.flush()
        rejected = False
        try:
            reserve(db, gen, context)
        except ValueError:
            rejected = True
        check(rejected, "Session allowance denies a new reservation")
        db.rollback()
    # Exercise the same advisory-lock reservation in separate committed database transactions.
    # No live mode or key is permitted while this disposable scenario owns the allowance row.
    if settings.live_ai_enabled:
        raise RuntimeError("Run allowance concurrency verification without live AI configuration.")
    with SessionLocal() as db:
        gen = db.get(GenerationRun, UUID(budget_run["id"]))
        reserve(db, gen, context)
        amount, month = gen.charge_micros, gen.usage["month"]
        db.rollback()
    with engine.begin() as db:
        previous = db.execute(
            text("SELECT allocated_micros,blocked FROM usage_month WHERE month=:m"), {"m": month}
        ).first()
        db.execute(
            text(
                "INSERT INTO usage_month(month,allocated_micros,blocked) VALUES(:m,:v,false) ON CONFLICT(month) DO UPDATE SET allocated_micros=:v,blocked=false"
            ),
            {"m": month, "v": 20_000_000 - amount},
        )

    def allocate(run_id):
        with SessionLocal() as db:
            try:
                gen = db.get(GenerationRun, UUID(run_id))
                reserve(db, gen, context)
                db.commit()
                return True
            except ValueError:
                db.rollback()
                return False

    try:
        with ThreadPoolExecutor(2) as pool:
            outcomes = list(pool.map(allocate, [budget_run["id"], stale["id"]]))
        check(
            outcomes.count(True) == 1 and outcomes.count(False) == 1,
            "Concurrent PostgreSQL reservations cannot overspend remaining monthly allowance",
        )
    finally:
        with engine.begin() as db:
            if previous:
                db.execute(
                    text("UPDATE usage_month SET allocated_micros=:a,blocked=:b WHERE month=:m"),
                    {"m": month, "a": previous.allocated_micros, "b": previous.blocked},
                )
            else:
                db.execute(text("DELETE FROM usage_month WHERE month=:m"), {"m": month})
    print(
        f"\n{len(checks)} assertions passed. Real HTTP/PostgreSQL/workers; explicit fixture generation, no provider requests or AI quality claims."
    )
finally:
    with engine.begin() as db:
        for workspace in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": workspace})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
