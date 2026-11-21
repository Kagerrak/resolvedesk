"""Repository-approved synthetic sources, indexed privately for each public demo."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .evaluation_dataset import load_dataset
from .knowledge_worker import fixture_embedding, sections
from .models import (
    DocumentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeJob,
    Message,
    Ticket,
)
from .operation_history import record

VERSION = "public-seed-v1"
ARTICLE_IDS = ("roles", "project-invites", "invoices", "invitation-expiry")


def seed(db, workspace):
    # Trusted application setup only; visitors cannot publish arbitrary content.
    dataset, _ = load_dataset()
    selected = [a for a in dataset.articles if a.id in ARTICLE_IDS]
    if len(selected) != len(ARTICLE_IDS):
        raise ValueError("The approved synthetic corpus is unavailable.")
    for article in selected:
        content = article.content()
        digest = hashlib.sha256(content.encode()).hexdigest()
        doc_id, version_id, job_id = uuid4(), uuid4(), uuid4()
        now = datetime.now(UTC)
        db.add(
            KnowledgeDocument(
                id=doc_id,
                workspace_id=workspace.id,
                title=article.title,
                created_by="system:" + VERSION,
                created_at=now,
            )
        )
        db.flush()
        db.add(
            DocumentVersion(
                id=version_id,
                workspace_id=workspace.id,
                document_id=doc_id,
                filename=article.id + ".md",
                content=content,
                content_hash=digest,
                status="published",
                published_by="system:" + VERSION,
                published_at=now,
            )
        )
        db.flush()
        # The actual parser/embedding functions run here; there is no simulated indexing attempt.
        for ordinal, (heading, text) in enumerate(sections(content, True), 1):
            db.add(
                KnowledgeChunk(
                    workspace_id=workspace.id,
                    version_id=version_id,
                    ordinal=ordinal,
                    heading=heading,
                    content=text,
                    embedding=fixture_embedding(heading + " " + text),
                )
            )
        db.add(
            KnowledgeJob(
                id=job_id,
                workspace_id=workspace.id,
                version_id=version_id,
                status="succeeded",
                attempts=1,
                created_at=now,
            )
        )
        record(db, workspace.id, job_id, "indexing", "queued", actor_id=None)
        record(db, workspace.id, job_id, "indexing", "started", actor_id=None, attempt=1)
        record(db, workspace.id, job_id, "indexing", "completed", actor_id=None, attempt=1)
        record(db, workspace.id, doc_id, "source", "publish", actor_id=None)
    cases = {c.id: c for c in dataset.cases}
    for index, (key, name, email) in enumerate(
        (
            ("c03", "Jordan Lee", "jordan@example.com"),
            ("c49", "Casey Chen", "casey@example.com"),
        )
    ):
        case = cases[key]
        ticket_id = uuid4()
        created = datetime.now(UTC) - timedelta(minutes=1, seconds=index)
        db.add(
            Ticket(
                id=ticket_id,
                workspace_id=workspace.id,
                number=1043 + index,
                subject=case.subject,
                customer_name=name,
                customer_email=email,
                created_at=created,
            )
        )
        db.flush()
        db.add(
            Message(
                workspace_id=workspace.id,
                ticket_id=ticket_id,
                sender_name=name,
                sender_email=email,
                body=case.body,
                created_at=created,
            )
        )
    db.flush()
