"""Workspace-private knowledge upload, inspection and Admin publication."""

import base64
import binascii
import hashlib
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .database import database
from .identity import Identity, identity
from .inbox import membership
from .models import (
    DocumentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeJob,
    Membership,
    Workspace,
)

router = APIRouter()
DB = Annotated[Session, Depends(database)]
Visitor = Annotated[Identity, Depends(identity)]
MAX_BYTES = 256 * 1024


class Upload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=120)
    filename: str = Field(min_length=1, max_length=180)
    content_base64: str = Field(max_length=2800000)


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)


def require_admin(db: Session, workspace_id: UUID, visitor: Identity):
    member = db.scalar(
        select(Membership)
        .join(Workspace)
        .where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == visitor.user_id,
            Workspace.expires_at.is_(None) | (Workspace.expires_at > datetime.now(UTC)),
        )
        .with_for_update(read=True, of=[Membership, Workspace])
    )
    if not member:
        raise HTTPException(404, "Workspace not found or no longer available.")
    if member.role != "admin":
        raise HTTPException(403, "Only an Admin can manage knowledge.")
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"published-snapshot:{workspace_id}"},
    )


def document_pair(db: Session, workspace_id: UUID, document_id: UUID, lock=False):
    query = select(KnowledgeDocument).where(
        KnowledgeDocument.workspace_id == workspace_id, KnowledgeDocument.id == document_id
    )
    if lock:
        query = query.with_for_update()
    doc = db.scalar(query)
    if not doc:
        raise HTTPException(404, "Knowledge document not found.")
    query_version = select(DocumentVersion).where(
        DocumentVersion.workspace_id == workspace_id, DocumentVersion.document_id == document_id
    )
    if lock:
        query_version = query_version.with_for_update()
    version = db.scalar(query_version)
    if not version:
        raise HTTPException(404, "Document version not found.")
    return doc, version


def document_view(doc: KnowledgeDocument, version: DocumentVersion):
    return {
        "id": doc.id,
        "title": doc.title,
        "revision": doc.revision,
        "archived": doc.archived,
        "status": "archived" if doc.archived else version.status,
        "version_id": version.id,
        "version_number": version.number,
        "filename": version.filename,
        "embedding_model": version.embedding_model,
        "published_at": version.published_at,
        "page_count": version.page_count,
        "created_at": doc.created_at,
    }


@router.get("/workspaces/{workspace_id}/knowledge")
def list_documents(workspace_id: UUID, db: DB, visitor: Visitor):
    member = membership(db, workspace_id, visitor)
    query = (
        select(KnowledgeDocument, DocumentVersion)
        .join(
            DocumentVersion,
            (DocumentVersion.document_id == KnowledgeDocument.id)
            & (DocumentVersion.workspace_id == KnowledgeDocument.workspace_id),
        )
        .where(KnowledgeDocument.workspace_id == workspace_id)
    )
    if member.role != "admin":
        query = query.where(
            KnowledgeDocument.archived.is_(False), DocumentVersion.status == "published"
        )
    return [
        document_view(d, v)
        for d, v in db.execute(query.order_by(KnowledgeDocument.created_at.desc()))
    ]


@router.post("/workspaces/{workspace_id}/knowledge", status_code=201)
def upload(workspace_id: UUID, payload: Upload, db: DB, visitor: Visitor):
    require_admin(db, workspace_id, visitor)
    filename = PurePath(payload.filename).name
    extension = PurePath(filename).suffix.lower()
    if extension not in (".md", ".txt", ".pdf"):
        raise HTTPException(
            415, "Upload Markdown (.md), plain text (.txt), or a text-based PDF (.pdf)."
        )
    try:
        raw = base64.b64decode(payload.content_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(
            422, "The file could not be decoded. Select it again and retry."
        ) from None
    limit = 2 * 1024 * 1024 if extension == ".pdf" else MAX_BYTES
    if len(raw) > limit:
        raise HTTPException(413, "Keep PDF uploads under 2 MB and text uploads under 256 KB.")
    if extension == ".pdf":
        if not raw.startswith(b"%PDF-"):
            raise HTTPException(422, "This file is not a valid PDF. Export a new text-based PDF.")
        content = ""
    else:
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeError:
            raise HTTPException(422, "Save the file as UTF-8 text and upload it again.") from None
        if not content.strip() or "\x00" in content:
            raise HTTPException(422, "Provide a non-empty UTF-8 text document.")
    if not payload.title.strip():
        raise HTTPException(422, "Provide a document title.")
    doc = KnowledgeDocument(
        workspace_id=workspace_id,
        title=payload.title.strip(),
        created_by=visitor.user_id,
        created_at=datetime.now(UTC),
    )
    db.add(doc)
    db.flush()
    version = DocumentVersion(
        workspace_id=workspace_id,
        document_id=doc.id,
        filename=filename,
        source_bytes=raw if extension == ".pdf" else None,
        content=content,
        content_hash=hashlib.sha256(raw).hexdigest(),
    )
    db.add(version)
    db.flush()
    db.add(
        KnowledgeJob(workspace_id=workspace_id, version_id=version.id, created_at=datetime.now(UTC))
    )
    db.commit()
    return document_view(doc, version)


@router.get("/workspaces/{workspace_id}/knowledge/{document_id}")
def inspect_document(workspace_id: UUID, document_id: UUID, db: DB, visitor: Visitor):
    member = membership(db, workspace_id, visitor)
    doc, version = document_pair(db, workspace_id, document_id, lock=True)
    if member.role != "admin" and (doc.archived or version.status != "published"):
        raise HTTPException(404, "Knowledge document not found.")
    chunks = db.scalars(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.workspace_id == workspace_id, KnowledgeChunk.version_id == version.id)
        .order_by(KnowledgeChunk.ordinal)
    ).all()
    job = db.scalar(
        select(KnowledgeJob).where(
            KnowledgeJob.version_id == version.id, KnowledgeJob.workspace_id == workspace_id
        )
    )
    return {
        **document_view(doc, version),
        "sections": [
            {
                "id": c.id,
                "ordinal": c.ordinal,
                "heading": c.heading,
                "content": c.content,
                "page_number": c.page_number,
            }
            for c in chunks
        ],
        "job": {"status": job.status, "attempts": job.attempts, "error": job.error}
        if job
        else None,
    }


@router.post("/workspaces/{workspace_id}/knowledge/{document_id}/{action}")
def command(
    workspace_id: UUID, document_id: UUID, action: str, payload: Command, db: DB, visitor: Visitor
):
    require_admin(db, workspace_id, visitor)
    doc, version = document_pair(db, workspace_id, document_id, lock=True)
    if payload.expected_revision != doc.revision:
        raise HTTPException(409, "This document changed. Refresh it before trying again.")
    if action == "archive":
        doc.archived = True
    elif doc.archived:
        raise HTTPException(409, "This document is archived. Upload a new document to replace it.")
    elif action == "publish":
        count = db.scalar(
            select(func.count())
            .select_from(KnowledgeChunk)
            .where(
                KnowledgeChunk.workspace_id == workspace_id, KnowledgeChunk.version_id == version.id
            )
        )
        if version.status != "ready" or not count:
            raise HTTPException(
                409, "Wait for successful indexing and inspect the sections before publishing."
            )
        version.status = "published"
        version.published_at = datetime.now(UTC)
        version.published_by = visitor.user_id
    elif action == "retry":
        job = db.scalar(
            select(KnowledgeJob).where(KnowledgeJob.version_id == version.id).with_for_update()
        )
        if not job or job.status != "failed" or job.attempts >= 3:
            raise HTTPException(
                409,
                "This job cannot be retried. After three failed attempts, upload a corrected file.",
            )
        job.status = "queued"
        job.error = None
        job.lease_until = None
        job.lease_token = None
        version.status = "queued"
    else:
        raise HTTPException(404, "Action not found.")
    doc.revision += 1
    db.commit()
    return document_view(doc, version)


@router.get("/workspaces/{workspace_id}/knowledge/{document_id}/download")
def download(workspace_id: UUID, document_id: UUID, db: DB, visitor: Visitor):
    member = membership(db, workspace_id, visitor)
    doc, version = document_pair(db, workspace_id, document_id, lock=True)
    if member.role != "admin" and (doc.archived or version.status != "published"):
        raise HTTPException(404, "Knowledge document not found.")
    return Response(
        content=version.source_bytes
        if version.source_bytes is not None
        else version.content.encode("utf-8"),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''"
            + quote(version.filename, safe=""),
            "Content-Security-Policy": "sandbox",
            "X-Content-Type-Options": "nosniff",
        },
    )
