"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { api, ApiError, type Workspace } from "@/lib/api";

type Document = {
  id: string;
  title: string;
  revision: number;
  archived: boolean;
  status: string;
  version_id: string;
  version_number: number;
  filename: string;
  page_count: number | null;
  embedding_model: string;
  published_at: string | null;
  created_at: string;
};
type Detail = Document & {
  sections: {
    id: string;
    ordinal: number;
    heading: string;
    content: string;
    page_number: number | null;
  }[];
  job: { status: string; attempts: number; error: string | null } | null;
};

export default function KnowledgePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const selection = useRef({ workspace: "", document: "" });
  const workspace = workspaces.find((w) => w.id === workspaceId);
  const admin = workspace?.role === "admin";
  function report(reason: unknown) {
    if (reason instanceof Error && reason.name === "AbortError") return;
    if (
      reason instanceof ApiError &&
      [401, 403, 404, 410].includes(reason.status)
    ) {
      setDetail(null);
      setDocuments([]);
      if (reason.status === 401) {
        setWorkspaces([]);
        setWorkspaceId("");
      }
    }
    setError(
      reason instanceof Error
        ? reason.message
        : "Knowledge could not be loaded. Try again.",
    );
    setLoading(false);
  }
  useEffect(() => {
    if (detail?.id)
      document.querySelector<HTMLElement>(".source-detail h2")?.focus();
  }, [detail?.id]);

  useEffect(() => {
    const controller = new AbortController();
    api<Workspace[]>("workspaces", "GET", controller.signal)
      .then((rows) => {
        setWorkspaces(rows);
        const wanted = new URLSearchParams(window.location.search).get(
          "workspace",
        );
        const id = rows.find((w) => w.id === wanted)?.id ?? rows[0]?.id ?? "";
        selection.current = { workspace: id, document: "" };
        setWorkspaceId(id);
        setSelected("");
        setDetail(null);
        if (!id) setLoading(false);
      })
      .catch((reason) => {
        report(reason);
      });
    return () => controller.abort();
  }, [retry]);
  useEffect(() => {
    if (!workspaceId) return;
    const controller = new AbortController();
    api<Document[]>(
      `workspaces/${workspaceId}/knowledge`,
      "GET",
      controller.signal,
    )
      .then((rows) => {
        if (selection.current.workspace !== workspaceId) return;
        setDocuments(rows);
        setLoading(false);
      })
      .catch((reason) => {
        report(reason);
      });
    return () => controller.abort();
  }, [workspaceId, retry]);
  useEffect(() => {
    if (!selected || !workspaceId) return;
    const controller = new AbortController();
    api<Detail>(
      `workspaces/${workspaceId}/knowledge/${selected}`,
      "GET",
      controller.signal,
    )
      .then((row) => {
        if (
          selection.current.workspace === workspaceId &&
          selection.current.document === selected
        )
          setDetail(row);
      })
      .catch((reason) => {
        report(reason);
      });
    return () => controller.abort();
  }, [workspaceId, selected]);
  async function refresh(clearNotice = true) {
    if (clearNotice) setNotice("");
    const current = { ...selection.current };
    setBusy(true);
    setError("");
    try {
      const rows = await api<Document[]>(
        `workspaces/${current.workspace}/knowledge`,
      );
      if (selection.current.workspace !== current.workspace) return;
      setDocuments(rows);
      if (
        current.document &&
        !rows.some((doc) => doc.id === current.document)
      ) {
        selection.current.document = "";
        setSelected("");
        setDetail(null);
        setNotice(
          "The selected source is no longer available in this workspace.",
        );
        return;
      }
      const row = current.document
        ? await api<Detail>(
            `workspaces/${current.workspace}/knowledge/${current.document}`,
          )
        : null;
      if (
        selection.current.workspace === current.workspace &&
        selection.current.document === current.document
      )
        setDetail(row);
    } catch (reason) {
      report(reason);
    } finally {
      setBusy(false);
    }
  }
  async function upload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setNotice("");
    if (
      file.size > (/\.pdf$/i.test(file.name) ? 2 * 1024 * 1024 : 256 * 1024)
    ) {
      setError(
        "This file is too large. Keep PDFs under 2 MB and text files under 256 KB.",
      );
      return;
    }
    if (!/\.(md|txt|pdf)$/i.test(file.name)) {
      setError(
        "Choose a Markdown (.md), plain text (.txt) or text-based PDF (.pdf) file.",
      );
      return;
    }
    setBusy(true);
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (const byte of bytes) binary += String.fromCharCode(byte);
      const row = await api<Document>(
        `workspaces/${workspaceId}/knowledge`,
        "POST",
        undefined,
        { title, filename: file.name, content_base64: btoa(binary) },
      );
      setDocuments((rows) => [row, ...rows]);
      selection.current.document = row.id;
      setSelected(row.id);
      setDetail(null);
      setFile(null);
      setTitle("");
      const input = document.querySelector<HTMLInputElement>("#knowledge-file");
      if (input) input.value = "";
      setNotice(
        "File saved privately. Indexing is queued; refresh to check progress.",
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Upload failed. Your file is still selected for retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function command(action: "publish" | "archive" | "retry") {
    if (!detail) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(
        `workspaces/${workspaceId}/knowledge/${detail.id}/${action}`,
        "POST",
        undefined,
        { expected_revision: detail.revision },
      );
      setNotice(
        action === "publish"
          ? "Version published. Workspace members can now use these sections."
          : action === "archive"
            ? "Document archived. It is no longer available as published knowledge."
            : "Indexing queued again. Refresh to check progress.",
      );
      await refresh(false);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not complete this action. Refresh and try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="knowledge-shell">
      <header className="app-header">
        <Brand />
        <Link className="secondary" href="/inbox">
          Inbox
        </Link>
        <div className="header-actions">
          <span className="badge">Synthetic demo</span>
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="knowledge-main">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">
              Workspace knowledge · Fixture embeddings
            </span>
            <h1>Knowledge</h1>
            <p className="muted">
              Inspect the source before it becomes an answer.
            </p>
          </div>
          <label>
            Workspace
            <select
              className="workspace-select"
              value={workspaceId}
              disabled={busy || !workspaces.length}
              onChange={(e) => {
                const id = e.target.value;
                selection.current = { workspace: id, document: "" };
                setWorkspaceId(id);
                setSelected("");
                setDetail(null);
                setDocuments([]);
                setError("");
                setNotice("");
                setLoading(true);
                setFile(null);
                setTitle("");
                window.history.replaceState(
                  null,
                  "",
                  `/knowledge?workspace=${id}`,
                );
              }}
            >
              {!workspaces.length && <option>No workspace</option>}
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </label>
        </header>
        {error && (
          <div role="alert" className="alert error">
            {error}{" "}
            <button
              className="secondary"
              disabled={busy}
              onClick={() => {
                setError("");
                setLoading(true);
                setRetry((v) => v + 1);
              }}
            >
              Reload knowledge
            </button>{" "}
            <Link href="/">Demo entry</Link>
          </div>
        )}
        {notice && (
          <p role="status" className="save-notice">
            {notice}
          </p>
        )}
        {admin ? (
          <form className="knowledge-upload" onSubmit={upload}>
            <h2>Add a source</h2>
            <p className="small muted">
              Markdown or plain text: UTF-8, up to 256 KB. Text-based PDFs: up
              to 2 MB and 20 pages. Scanned or encrypted PDFs are not supported.
              Use synthetic English content in this local preview. Only an Admin
              can publish.
            </p>
            <label>
              Document title
              <input
                required
                maxLength={120}
                value={title}
                disabled={busy}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label>
              Source file
              <input
                id="knowledge-file"
                type="file"
                accept=".md,.txt,.pdf,text/plain,text/markdown,application/pdf"
                disabled={busy}
                required
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <button className="primary" disabled={busy || !file}>
              Upload for inspection
            </button>
          </form>
        ) : (
          <p className="alert">
            {workspace
              ? "You can read published sources. An Admin manages uploads and publication."
              : "Choose an active workspace from the demo entry."}
          </p>
        )}
        <div className="knowledge-layout">
          <section aria-label="Knowledge documents">
            <div className="queue-heading">
              <h2>{admin ? "All documents" : "Published documents"}</h2>
              <button
                className="secondary"
                disabled={busy || !workspaceId}
                onClick={() => void refresh()}
              >
                Refresh
              </button>
            </div>
            {loading ? (
              <p role="status">Loading knowledge…</p>
            ) : !documents.length ? (
              <p className="muted">
                {error
                  ? "Knowledge could not be loaded."
                  : "No published sources yet. Admins can upload a file, inspect its sections and publish."}
              </p>
            ) : (
              documents.map((doc) => (
                <button
                  className="document-row"
                  key={doc.id}
                  aria-pressed={selected === doc.id}
                  disabled={busy}
                  onClick={() => {
                    if (selection.current.document === doc.id) return;
                    selection.current.document = doc.id;
                    setSelected(doc.id);
                    setDetail(null);
                    setError("");
                    setNotice("");
                  }}
                >
                  <strong>{doc.title}</strong>
                  <span className="small muted">
                    Version {doc.version_number} · {doc.status}
                  </span>
                </button>
              ))
            )}
          </section>
          <section className="source-detail" aria-label="Source inspection">
            {detail ? (
              <>
                <span className="eyebrow">
                  {detail.filename} · Version {detail.version_number}
                </span>
                <button
                  className="secondary source-back"
                  onClick={() =>
                    document
                      .querySelector<HTMLElement>(
                        ".document-row[aria-pressed=true]",
                      )
                      ?.focus()
                  }
                >
                  Back to documents
                </button>
                <h2 tabIndex={-1}>{detail.title}</h2>
                <span className="badge">{detail.status}</span>
                <p>
                  <a
                    href={`/api/backend/workspaces/${workspaceId}/knowledge/${detail.id}/download`}
                    download
                  >
                    Download original source
                  </a>
                  {detail.page_count && ` · ${detail.page_count} pages`}
                </p>
                <p className="small muted">
                  Fixture embeddings · deterministic local indexing · no AI
                  provider calls
                </p>
                {detail.job?.error && (
                  <div className="alert error" role="alert">
                    {detail.job.error}
                  </div>
                )}
                {["queued", "processing"].includes(detail.status) && (
                  <p role="status">
                    {detail.status === "queued"
                      ? "Waiting for the knowledge worker."
                      : "Parsing and indexing this version."}{" "}
                    Refresh to check progress.
                  </p>
                )}
                {admin && (
                  <div className="form-actions">
                    {detail.status === "ready" && (
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() => void command("publish")}
                      >
                        Publish version {detail.version_number}
                      </button>
                    )}
                    {detail.status === "failed" &&
                      detail.job &&
                      detail.job.attempts < 3 && (
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => void command("retry")}
                        >
                          Retry indexing
                        </button>
                      )}
                    {!detail.archived && (
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={() => void command("archive")}
                      >
                        Archive document
                      </button>
                    )}
                  </div>
                )}
                <h3 className="sections-heading">
                  {detail.sections.length} indexed sections
                </h3>
                {detail.sections.map((section) => (
                  <article className="source-section" key={section.id}>
                    <h3>
                      {section.ordinal}.{" "}
                      {section.page_number
                        ? `Page ${section.page_number}`
                        : section.heading}
                    </h3>
                    <p>{section.content}</p>
                  </article>
                ))}
              </>
            ) : (
              <p className="muted">
                {selected
                  ? error
                    ? "Source could not be loaded. Reload knowledge to recover."
                    : "Loading source…"
                  : "Choose a document to inspect its sections."}
              </p>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
