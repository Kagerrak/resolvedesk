"""Exact pgvector ranking in fixture mode; citations always recheck current access."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from .inbox import membership, ticket_in_workspace
from .knowledge import DB, Visitor
from .knowledge_worker import fixture_embedding
from .models import (
    DocumentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    Message,
    RetrievalResult,
    RetrievalRun,
)

router = APIRouter()
MODEL = "fixture-hash-v1"
LIMIT = 5
MAX_DISTANCE = 0.65  # Fixture selection threshold, not a calibrated confidence score.


def published_chunks(workspace_id):
    return (
        select(KnowledgeChunk, DocumentVersion, KnowledgeDocument)
        .join(
            DocumentVersion,
            (DocumentVersion.id == KnowledgeChunk.version_id)
            & (DocumentVersion.workspace_id == KnowledgeChunk.workspace_id),
        )
        .join(
            KnowledgeDocument,
            (KnowledgeDocument.id == DocumentVersion.document_id)
            & (KnowledgeDocument.workspace_id == DocumentVersion.workspace_id),
        )
        .where(
            KnowledgeChunk.workspace_id == workspace_id,
            DocumentVersion.status == "published",
            DocumentVersion.embedding_model == MODEL,
            KnowledgeDocument.archived.is_(False),
        )
    )


def run_view(db, run):
    results = []
    for result in db.scalars(
        select(RetrievalResult)
        .where(RetrievalResult.workspace_id == run.workspace_id, RetrievalResult.run_id == run.id)
        .order_by(RetrievalResult.rank)
    ):
        row = db.execute(
            published_chunks(run.workspace_id).where(
                KnowledgeChunk.id == result.chunk_id, DocumentVersion.id == result.version_id
            )
        ).first()
        results.append(
            {
                "id": result.id,
                "rank": result.rank,
                "available": row is not None,
                "title": row[2].title if row else "Source no longer available",
                "version_id": result.version_id,
                "version_number": row[1].number if row else None,
                "heading": row[0].heading if row else None,
                "excerpt": row[0].content if row else None,
                "page_number": row[0].page_number if row else None,
            }
        )
    return {
        "id": run.id,
        "ticket_revision": run.ticket_revision,
        "created_at": run.created_at,
        "embedding_model": run.embedding_model,
        "source_versions": run.source_versions,
        "ranking": run.ranking,
        "results": results,
    }


@router.post("/workspaces/{workspace_id}/tickets/{ticket_id}/retrievals", status_code=201)
def retrieve(workspace_id: UUID, ticket_id: UUID, db: DB, visitor: Visitor):
    member = membership(db, workspace_id, visitor)
    if member.role == "viewer":
        raise HTTPException(403, "Viewers can inspect saved evidence but cannot run retrieval.")
    ticket = ticket_in_workspace(db, workspace_id, ticket_id)
    messages = db.scalars(
        select(Message)
        .where(Message.workspace_id == workspace_id, Message.ticket_id == ticket_id)
        .order_by(Message.created_at.desc(), Message.id)
        .limit(3)
    ).all()
    query = ticket.subject + "\n" + "\n".join(m.body[:4000] for m in reversed(messages))
    vector = fixture_embedding(query)
    distance = KnowledgeChunk.embedding.cosine_distance(vector)
    # Exact filtered search avoids approximate-index filtering/recall surprises at demo scale.
    rows = db.execute(
        published_chunks(workspace_id)
        .add_columns(distance.label("distance"))
        .where(distance <= MAX_DISTANCE)
        .order_by(distance, KnowledgeChunk.id)
        .limit(LIMIT)
        .with_for_update(read=True, of=[KnowledgeDocument, DocumentVersion])
    ).all()
    run = RetrievalRun(
        workspace_id=workspace_id,
        ticket_id=ticket_id,
        ticket_revision=ticket.revision,
        query=query,
        embedding_model=MODEL,
        source_versions=sorted({str(row[1].id) for row in rows}),
        ranking={"method": "exact-cosine-v1", "limit": LIMIT, "max_distance": MAX_DISTANCE},
        created_by=visitor.user_id,
        created_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()
    for rank, (chunk, version, doc, value) in enumerate(rows, 1):
        db.add(
            RetrievalResult(
                workspace_id=workspace_id,
                run_id=run.id,
                version_id=version.id,
                chunk_id=chunk.id,
                rank=rank,
                distance=float(value),
            )
        )
    db.flush()
    result = run_view(db, run)
    db.commit()
    return result


@router.get("/workspaces/{workspace_id}/tickets/{ticket_id}/retrievals/latest")
def latest(workspace_id: UUID, ticket_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    ticket_in_workspace(db, workspace_id, ticket_id)
    run = db.scalar(
        select(RetrievalRun)
        .where(RetrievalRun.workspace_id == workspace_id, RetrievalRun.ticket_id == ticket_id)
        .order_by(RetrievalRun.created_at.desc(), RetrievalRun.id)
        .limit(1)
    )
    return run_view(db, run) if run else None


@router.get("/workspaces/{workspace_id}/citations/{citation_id}")
def citation(workspace_id: UUID, citation_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    result = db.scalar(
        select(RetrievalResult).where(
            RetrievalResult.workspace_id == workspace_id, RetrievalResult.id == citation_id
        )
    )
    if not result:
        raise HTTPException(404, "Citation not found or no longer available.")
    row = db.execute(
        published_chunks(workspace_id)
        .where(KnowledgeChunk.id == result.chunk_id, DocumentVersion.id == result.version_id)
        .with_for_update(read=True, of=[KnowledgeDocument, DocumentVersion])
    ).first()
    if not row:
        raise HTTPException(404, "Citation not found or no longer available.")
    chunk, version, doc = row
    return {
        "title": doc.title,
        "document_id": doc.id,
        "version_id": version.id,
        "version_number": version.number,
        "heading": chunk.heading,
        "page_number": chunk.page_number,
        "content": chunk.content,
        "ordinal": chunk.ordinal,
        "filename": version.filename,
    }
