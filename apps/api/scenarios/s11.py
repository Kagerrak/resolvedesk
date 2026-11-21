"""Post-implementation actual HTTP/PostgreSQL evaluation and durable-worker journeys."""

import time
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.evaluation_worker import run_once
from resolvedesk.knowledge_worker import run_once as index_once
from resolvedesk.local_admin import grant

WEB = "http://localhost:3000"
users, workspaces, checks = [], [], []


def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label, flush=True)


def sql(statement, **values):
    with engine.begin() as db:
        return db.execute(text(statement), values)


def scalar(statement, **values):
    with engine.connect() as db:
        return db.scalar(text(statement), values)


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
    return client, user, w, f"/api/backend/workspaces/{w}"


def start(client, root, method="exact-cosine-v1", request=None):
    return client.post(
        root + "/evaluations",
        json={"request_id": request or str(uuid4()), "split": "tuning", "method": method},
    )


def finish(run_id):
    for _ in range(15):
        if not run_once(target_run_id=UUID(run_id)):
            break
        if scalar("SELECT status FROM evaluation_run WHERE id=:r", r=run_id) in (
            "completed",
            "failed",
        ):
            break


try:
    a, ua, wa, root = visitor()
    b, ub, wb, other = visitor()
    check(start(a, root).status_code == 403, "Agent cannot prepare evaluation corpus")
    grant(UUID(wa))
    metadata = a.get(root + "/evaluation-dataset").json()
    check(
        metadata["article_count"] == 24
        and metadata["case_count"] == 50
        and metadata["held_out_count"] == 38,
        "Dataset counts come from versioned authored inputs",
    )
    check(a.get(root + "/evaluations").json() == [], "Empty results are explicit")
    check(
        a.post(
            root + "/evaluations", json={"request_id": str(uuid4()), "mode": "deepseek_sample"}
        ).status_code
        == 422,
        "Public API forbids paid mode rather than silently accepting it",
    )
    check(
        a.post(
            root + "/evaluations",
            json={"request_id": str(uuid4()), "dataset_version": "../../.env"},
        ).status_code
        == 422,
        "Dataset identifiers cannot read arbitrary local files",
    )
    request = str(uuid4())
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda _: start(a, root, request=request), range(2)))
    for response in responses:
        response.raise_for_status()
    run_id = responses[0].json()["id"]
    path = root + f"/evaluations/{run_id}"
    check(
        responses[1].json()["id"] == run_id
        and scalar("SELECT count(*) FROM evaluation_run WHERE workspace_id=:w", w=wa) == 1,
        "Concurrent repeated intent creates one durable evaluation",
    )
    check(
        start(a, root, method="bm25-v1", request=request).status_code == 409,
        "Request identity binds exact method and dataset intent",
    )
    check(start(a, root).status_code == 409, "Concurrent different evaluation is rejected")
    check(
        b.get(root + "/evaluations").status_code == 404 and b.get(path).status_code == 404,
        "Other workspace cannot list or open evaluation records",
    )
    first = a.get(path + "/cases").json()["items"][0]
    check(
        b.get(path + f"/cases/{first['id']}").status_code == 404,
        "Case details cannot cross workspace authorization",
    )
    sql("UPDATE evaluation_run SET mode='deepseek_sample' WHERE id=:r", r=run_id)
    check(
        not run_once(target_run_id=UUID(run_id))
        and scalar("SELECT status FROM evaluation_run WHERE id=:r", r=run_id) == "queued",
        "Default worker leaves paid evaluation untouched",
    )
    sql("UPDATE evaluation_run SET mode='fixture' WHERE id=:r", r=run_id)
    try:
        run_once(target_run_id=UUID(run_id), allow_live=True)
    except ValueError:
        check(True, "Explicit live worker remains disabled without the local live gate")
    else:
        raise AssertionError("Run verification with LIVE_AI_ENABLED=false")
    check(
        run_once(target_run_id=UUID(run_id)),
        "Actual worker parses indexes publishes and evaluates first case",
    )
    first_detail = a.get(path + f"/cases/{first['id']}").json()
    check(
        first_detail["fixture_output"]["mode"] == "fixture"
        and first_detail["provider_output"] is None,
        "Fixture output persists separately without invented live metrics",
    )
    stored = a.get(path).json()
    check(
        len(stored["source_versions"]) == 24
        and "probe_marker" not in str(stored)
        and "PROBE_B_" not in str(stored),
        "Run exposes source hashes but never private probe marker",
    )
    check(
        scalar("SELECT count(*) FROM generation_run WHERE workspace_id=:w", w=wa) == 0
        and scalar("SELECT count(*) FROM draft_revision WHERE workspace_id=:w", w=wa) == 0,
        "Fixture simulations do not consume draft quota or create reply revisions",
    )
    check(
        a.post(
            path + f"/cases/{first['id']}/reviews",
            json={
                "request_id": str(uuid4()),
                "output_hash": first_detail["fixture_output"]["output_hash"],
                "reviewer_kind": "member",
                "verdict": "supported",
                "note": "Attempt to mislabel fixture as live quality",
            },
        ).status_code
        == 409,
        "Fixture output cannot be reviewed as live AI quality",
    )
    check(b.post(path + "/cancel").status_code == 404, "Foreign workspace cannot cancel a run")
    sql("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u", w=wa, u=ua)
    check(
        a.post(path + "/cancel").status_code == 403 and a.get(path).status_code == 200,
        "Viewer may inspect persisted results but cannot cancel",
    )
    grant(UUID(wa))
    controlled = scalar(
        "SELECT source_map->'conflicting-refunds'->>'document_id' FROM evaluation_run WHERE id=:r",
        r=run_id,
    )
    source = a.get(root + f"/knowledge/{controlled}").json()
    a.post(
        root + f"/knowledge/{controlled}/publish", json={"expected_revision": source["revision"]}
    ).raise_for_status()
    a.post(path + "/cancel").raise_for_status()
    cancelled = a.get(path).json()
    check(
        cancelled["status"] == "cancelled" and cancelled["summary"]["completed_cases"] == 1,
        "Cancel retains the measured completed-case denominator",
    )
    check(
        not run_once(target_run_id=UUID(run_id))
        and scalar("SELECT probe_workspace_id IS NULL FROM evaluation_run WHERE id=:r", r=run_id),
        "Cancelled worker does not advance and private probe is cleaned",
    )
    check(
        scalar("SELECT archived FROM knowledge_document WHERE id=:d", d=controlled),
        "Cancellation retires an actually published controlled conflict source",
    )
    second = start(a, root).json()["id"]
    run_once(target_run_id=UUID(second))
    sql(
        "UPDATE evaluation_run SET lease_token=:token,lease_until=now()-interval '1 second' WHERE id=:r",
        token=str(uuid4()),
        r=second,
    )
    finish(second)
    result = a.get(root + f"/evaluations/{second}").json()
    check(
        result["status"] == "completed" and result["summary"]["completed_cases"] == 12,
        "Fresh worker resumes actual durable expired lease and completes twelve cases",
    )
    check(
        result["summary"]["source_recall_at_5"]["denominator"] == 11
        and result["summary"]["provider"]["citation_validity"]["value"] is None
        and result["summary"]["timing"]["retrieval"]["count"] == 12,
        "Objective recall timing and zero-live denominators are explicit",
    )
    cases = a.get(root + f"/evaluations/{second}/cases", params={"offset": 10, "limit": 2}).json()
    check(
        cases["total"] == 12
        and len(cases["items"]) == 2
        and a.get(root + f"/evaluations/{second}/cases", params={"split": "held_out"}).json()[
            "total"
        ]
        == 0,
        "Case pagination and tuning versus held-out filters query stored records",
    )
    third = start(a, root, method="bm25-v1").json()["id"]
    finish(third)
    candidate = a.get(root + f"/evaluations/{third}").json()
    check(
        candidate["status"] == "completed" and candidate["method"] == "bm25-v1",
        "Frozen lexical candidate uses actual scoped published-source retrieval",
    )
    check(start(a, root).status_code == 429, "Three-run session limit enforced after completion")
    check(
        scalar("SELECT count(*) FROM message WHERE workspace_id=:w AND kind <> 'customer'", w=wa)
        == 0
        and scalar("SELECT count(*) FROM approval_record WHERE workspace_id=:w", w=wa) == 0,
        "Evaluation never sends a reply or applies unapproved ticket actions",
    )
    grant(UUID(wb))
    failure_id = start(b, other).json()["id"]
    sql(
        "UPDATE message SET body='Changed conversation' WHERE ticket_id=(SELECT ticket_id FROM evaluation_case WHERE run_id=:r ORDER BY case_key LIMIT 1)",
        r=failure_id,
    )
    run_once(target_run_id=UUID(failure_id))
    failed = b.get(other + f"/evaluations/{failure_id}").json()
    check(
        failed["status"] == "failed" and "conversation changed" in failed["error"],
        "Changed authored conversation fails closed before output or paid dispatch",
    )
    check(
        scalar("SELECT probe_workspace_id IS NULL FROM evaluation_run WHERE id=:r", r=failure_id),
        "Failed evaluation cleans private probe while retaining failed-case evidence",
    )
    changed_corpus = start(b, other).json()["id"]
    run_once(target_run_id=UUID(changed_corpus))
    import base64

    extra = b.post(
        other + "/knowledge",
        json={
            "title": "Unrelated synthetic source",
            "filename": "extra.md",
            "content_base64": base64.b64encode(
                b"# Extra source\n\nThis is outside the frozen evaluation corpus."
            ).decode(),
        },
    ).json()
    index_once(target_version_id=UUID(extra["version_id"]))
    doc = b.get(other + f"/knowledge/{extra['id']}").json()
    b.post(
        other + f"/knowledge/{extra['id']}/publish", json={"expected_revision": doc["revision"]}
    ).raise_for_status()
    run_once(target_run_id=UUID(changed_corpus))
    check(
        scalar("SELECT status FROM evaluation_run WHERE id=:r", r=changed_corpus) == "failed",
        "Publishing unrelated content fails the frozen-corpus evaluation closed",
    )
    # New requests preserve unrelated sources instead of overwriting them.
    check(
        start(b, other).status_code == 409, "Evaluation refuses to replace unrelated source content"
    )
    b.post(
        other + f"/knowledge/{extra['id']}/archive", json={"expected_revision": doc["revision"] + 1}
    ).raise_for_status()
    # Remove only this scenario-owned extra document to exercise a clean expiry request.
    sql("DELETE FROM knowledge_document WHERE id=:d", d=extra["id"])
    expiry_id = start(b, other).json()["id"]
    sql("UPDATE workspace SET expires_at=now()-interval '1 second' WHERE id=:w", w=wb)
    check(
        b.get(other + f"/evaluations/{expiry_id}").status_code == 404,
        "Expired session cannot inspect evaluation records",
    )
    run_once(target_run_id=UUID(expiry_id))
    check(
        scalar("SELECT status FROM evaluation_run WHERE id=:r", r=expiry_id) == "failed",
        "Worker rechecks current authorization after session expiry",
    )
    check(
        scalar("SELECT count(*) FROM generation_run WHERE workspace_id IN (:a,:b)", a=wa, b=wb)
        == 0,
        "All deterministic journeys remain free of paid requests and normal draft generations",
    )
    with engine.connect() as db:
        quota_cases = db.execute(
            text(
                "SELECT c.ticket_id,c.retrieval->>'id' AS retrieval_id,t.revision FROM evaluation_case c JOIN ticket t ON t.workspace_id=c.workspace_id AND t.id=c.ticket_id WHERE c.workspace_id=:w AND c.run_id=:r ORDER BY c.case_key"
            ),
            {"w": wa, "r": second},
        ).all()

    def request_generation(row):
        return a.post(
            root + f"/tickets/{row.ticket_id}/generations",
            json={
                "expected_revision": row.revision,
                "retrieval_id": row.retrieval_id,
                "request_id": str(uuid4()),
            },
        )

    for row in quota_cases[:9]:
        request_generation(row).raise_for_status()
    with ThreadPoolExecutor(2) as pool:
        final_slots = list(pool.map(request_generation, quota_cases[9:11]))
    check(
        sorted(r.status_code for r in final_slots) == [202, 429]
        and scalar("SELECT count(*) FROM generation_run WHERE workspace_id=:w", w=wa) == 10,
        "Concurrent distinct tickets cannot both consume the tenth generation slot",
    )
    check(
        scalar(
            "SELECT count(*) FROM generation_run WHERE workspace_id=:w AND mode='deepseek'", w=wa
        )
        == 0,
        "Quota race verification queues actual fixture jobs without paid calls",
    )
    print(f"\n{len(checks)} genuine HTTP/PostgreSQL/evaluation-worker assertions passed.")
finally:
    with engine.begin() as db:
        for w in workspaces:
            probes = db.scalars(
                text(
                    "SELECT probe_workspace_id FROM evaluation_run WHERE workspace_id=:w AND probe_workspace_id IS NOT NULL"
                ),
                {"w": w},
            ).all()
            for probe in probes:
                db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": probe})
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": w})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
