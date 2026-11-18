"""Post-implementation HTTP/PostgreSQL/pgvector retrieval verification; synthetic data only."""

import base64
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text

from resolvedesk.database import engine
from resolvedesk.knowledge_worker import run_once
from resolvedesk.local_admin import grant

WEB = "http://localhost:3000"
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
    ticket = client.get(f"/api/backend/workspaces/{workspace}/tickets").json()[0]["id"]
    return client, user, workspace, ticket


def source(client, workspace, title, body, publish=True, filename="guide.md"):
    route = f"/api/backend/workspaces/{workspace}/knowledge"
    response = client.post(
        route,
        json={
            "title": title,
            "filename": filename,
            "content_base64": base64.b64encode(body).decode(),
        },
    )
    response.raise_for_status()
    doc = response.json()
    while run_once():
        pass
    detail = client.get(f"{route}/{doc['id']}").json()
    check(detail["status"] == "ready", f"{title}: actual worker indexed source")
    if publish:
        response = client.post(
            f"{route}/{doc['id']}/publish", json={"expected_revision": detail["revision"]}
        )
        response.raise_for_status()
        detail = response.json()
    return detail


try:
    a, ua, wa, ta = visitor()
    b, ub, wb, tb = visitor()
    grant(UUID(wa))
    grant(UUID(wb))
    route = f"/api/backend/workspaces/{wa}/tickets/{ta}/retrievals"
    check(a.get(route + "/latest").json() is None, "No retrieval explicitly returns null")
    empty = a.post(route)
    empty.raise_for_status()
    check(empty.json()["results"] == [], "Empty published knowledge persists an empty evidence run")
    body = b"# Project access\nChanging Admin to Member does not remove explicit project membership. Restore project access by inviting the teammate to the quarterly planning project, without workspace admin permissions."
    private = source(b, wb, "PRIVATE B access canary", body)
    unpublished = source(a, wa, "Unpublished access", body, False)
    archived = source(a, wa, "Archived access", body)
    a.post(
        f"/api/backend/workspaces/{wa}/knowledge/{archived['id']}/archive",
        json={"expected_revision": archived["revision"]},
    ).raise_for_status()
    denied = a.post(route).json()
    check(
        denied["results"] == [], "Similar private B, unpublished and archived sources all excluded"
    )
    published = source(a, wa, "Published project access", body)
    pdf = source(
        a,
        wa,
        "Published PDF access",
        (Path(__file__).parent / "fixtures/access-guide.pdf").read_bytes(),
        filename="guide.pdf",
    )
    response = a.post(route)
    response.raise_for_status()
    run = response.json()
    check(
        run["ranking"] == {"method": "exact-cosine-v1", "limit": 5, "max_distance": 0.65},
        "Ranking method and selection parameters persist",
    )
    check(0 < len(run["results"]) <= 5, "Native pgvector returns bounded ranked excerpts")
    check(
        [r["rank"] for r in run["results"]] == list(range(1, len(run["results"]) + 1)),
        "Ranks persist in deterministic order",
    )
    allowed = {published["version_id"], pdf["version_id"]}
    check(
        set(run["source_versions"]) <= allowed
        and all(r["version_id"] in allowed for r in run["results"]),
        "Run stores only authorized published source versions",
    )
    check(any(r["page_number"] for r in run["results"]), "PDF results retain page references")
    check(a.get(route + "/latest").json() == run, "Saved evidence survives separate HTTP read")
    result = run["results"][0]
    cite = f"/api/backend/workspaces/{wa}/citations/{result['id']}"
    passage = a.get(cite)
    passage.raise_for_status()
    check(
        passage.json()["content"] == result["excerpt"],
        "Citation opens exact authorized version passage",
    )
    check(b.get(cite).status_code == 404, "Foreign member cannot open citation")
    check(
        a.get(f"/api/backend/workspaces/{wb}/citations/{result['id']}").status_code == 404,
        "Valid citation cannot be reparented across workspaces",
    )
    check(
        a.get(f"/api/backend/workspaces/{wa}/citations/{uuid4()}").status_code == 404,
        "Invented citation denied",
    )
    check(
        a.post(f"/api/backend/workspaces/{wa}/tickets/{tb}/retrievals").status_code == 404,
        "Foreign ticket ID denied",
    )
    check(b.get(route + "/latest").status_code == 404, "Foreign member cannot read persisted run")
    with engine.connect() as db:
        rows = db.execute(
            text(
                "SELECT rank,distance,version_id FROM retrieval_result WHERE run_id=:r ORDER BY rank"
            ),
            {"r": run["id"]},
        ).all()
        vector_type = db.scalar(
            text("SELECT pg_typeof(embedding)::text FROM knowledge_chunk LIMIT 1")
        )
        query = db.scalar(text("SELECT query FROM retrieval_run WHERE id=:r"), {"r": run["id"]})
    check(
        vector_type == "vector" and [r.distance for r in rows] == sorted(r.distance for r in rows),
        "PostgreSQL vector column and ascending cosine distances verified",
    )
    check("quarterly planning" in query, "Run persists actual ticket query provenance")
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='viewer' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    check(a.post(route).status_code == 403, "Viewer cannot create retrieval")
    check(
        a.get(cite).status_code == 200 and a.get(route + "/latest").status_code == 200,
        "Viewer can inspect saved evidence and citations",
    )
    with engine.begin() as db:
        db.execute(
            text("UPDATE membership SET role='admin' WHERE workspace_id=:w AND user_id=:u"),
            {"w": wa, "u": ua},
        )
    for doc in [published, pdf]:
        a.post(
            f"/api/backend/workspaces/{wa}/knowledge/{doc['id']}/archive",
            json={"expected_revision": doc["revision"]},
        ).raise_for_status()
    check(a.get(cite).status_code == 404, "Archive immediately revokes historical citation content")
    retired = a.get(route + "/latest").json()
    check(
        all(not r["available"] and r["excerpt"] is None for r in retired["results"]),
        "Historical run exposes retirement without retired text",
    )
    check(a.post(route).json()["results"] == [], "Future retrieval excludes retired versions")
    with engine.begin() as db:
        db.execute(
            text("DELETE FROM membership WHERE workspace_id=:w AND user_id=:u"), {"w": wa, "u": ua}
        )
    check(
        a.get(route + "/latest").status_code == 404 and a.get(cite).status_code == 404,
        "Membership revocation denies run and citation",
    )
    print(
        f"\n{len(checks)} assertions passed. Real HTTP/PostgreSQL/pgvector/worker; no mocks or provider quality claims."
    )
finally:
    with engine.begin() as db:
        for workspace in workspaces:
            db.execute(text("DELETE FROM workspace WHERE id=:w"), {"w": workspace})
        for user in users:
            db.execute(text('DELETE FROM "user" WHERE id=:u'), {"u": user})
