"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { api, type Workspace } from "@/lib/api";

type Operation = {
  id: string;
  kind: "indexing" | "generation" | "handling";
  title: string;
  resource_id: string;
  status: string;
  updated_at: string;
  revision: number;
  attempts: number;
  lease_until: string | null;
  mode: string;
  can_retry: boolean;
  lease_expired: boolean;
  next_action: string;
};
type Feed = {
  items: Operation[];
  total: number;
  offset: number;
  limit: number;
  source_operations_admin_only: boolean;
};
type Detail = Operation & {
  timeline: {
    phase: string;
    attempt: number;
    created_at: string;
    actor: string;
  }[];
  history_note: string;
};
const names: Record<string, string> = {
  queued: "Waiting for worker",
  processing: "In progress",
  succeeded: "Completed",
  failed: "Needs attention",
  cancelled: "Cancelled",
  escalated: "Human review needed",
  confirmed: "Recorded",
  archived: "Source archived",
  deleted: "Source deleted",
  started: "Indexing started",
  attempt_limit_reached: "Stopped after three attempts",
  retry_queued: "Retry requested",
  archive: "Source archived",
  delete: "Source content deleted",
  publish: "Source published",
  retry: "Source queued again",
  generation_requested: "Draft requested",
  confirmed_demo_reply: "Demo reply recorded · no email sent",
  confirmed_ticket_changes: "Ticket changes approved",
};
const label = (value: string) => names[value] ?? value.replaceAll("_", " ");
const kindName = (row: Operation) =>
  row.kind === "handling"
    ? row.mode === "simulated_delivery"
      ? "Demo reply"
      : "Ticket changes"
    : row.kind === "generation"
      ? "Draft generation"
      : "Source indexing";

export default function ActivityPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [kind, setKind] = useState("all");
  const [state, setState] = useState("all");
  const [offset, setOffset] = useState(0);
  const [feed, setFeed] = useState<Feed | null>(null);
  const [selected, setSelected] = useState<{ id: string; kind: string } | null>(
    null,
  );
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const workspace = workspaces.find((w) => w.id === workspaceId);
  useEffect(() => {
    const controller = new AbortController();
    api<Workspace[]>("workspaces", "GET", controller.signal)
      .then((rows) => {
        setWorkspaces(rows);
        const wanted = new URLSearchParams(window.location.search).get(
          "workspace",
        );
        setWorkspaceId(
          rows.find((w) => w.id === wanted)?.id ?? rows[0]?.id ?? "",
        );
        if (!rows.length) setLoading(false);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setError(reason.message);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (!workspaceId) return;
    const controller = new AbortController();
    api<Feed>(
      `workspaces/${workspaceId}/activity?kind=${kind}&state=${state}&offset=${offset}`,
      "GET",
      controller.signal,
    )
      .then((next) => {
        setFeed(next);
        setLoading(false);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setFeed(null);
          setDetail(null);
          setError(reason.message);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [workspaceId, kind, state, offset, refresh]);
  useEffect(() => {
    if (!selected || !workspaceId) return;
    const controller = new AbortController();
    api<Detail>(
      `workspaces/${workspaceId}/activity/${selected.kind}/${selected.id}`,
      "GET",
      controller.signal,
    )
      .then((next) => {
        setDetail(next);
        requestAnimationFrame(() => heading.current?.focus());
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setDetail(null);
          setError(reason.message);
        }
      });
    return () => controller.abort();
  }, [selected, workspaceId, refresh]);
  function reload() {
    setError("");
    setLoading(true);
    setRefresh((v) => v + 1);
  }
  function filters(nextKind: string, nextState: string) {
    setKind(nextKind);
    setState(nextState);
    setOffset(0);
    setSelected(null);
    setDetail(null);
    setFeed(null);
    setLoading(true);
    setError("");
  }
  async function retry() {
    if (!detail) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(
        `workspaces/${workspaceId}/activity/indexing/${detail.id}/retry`,
        "POST",
        undefined,
        { expected_revision: detail.revision },
      );
      setNotice(
        "Indexing queued again. The worker will resume safely; this does not publish the source.",
      );
      reload();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Recovery could not be confirmed. Refresh before retrying.",
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
        <Link
          className="secondary"
          href={`/knowledge?workspace=${workspaceId}`}
        >
          Knowledge
        </Link>
        <div className="header-actions">
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="knowledge-main">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">Workspace operations</span>
            <h1>Activity</h1>
            <p className="muted">
              Understand what happened and recover safely.
            </p>
          </div>
          <label>
            Workspace
            <select
              value={workspaceId}
              disabled={busy || !workspaces.length}
              onChange={(e) => {
                setWorkspaceId(e.target.value);
                setSelected(null);
                setDetail(null);
                setFeed(null);
                setOffset(0);
                setError("");
                setNotice("");
                setLoading(true);
                window.history.replaceState(
                  null,
                  "",
                  `/activity?workspace=${e.target.value}`,
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
        <p className="small muted">
          Gmail connection, sync and real-delivery recovery are not available
          yet. Demo replies never send email.
        </p>
        <div className="activity-filters">
          <label>
            Operation
            <select
              value={kind}
              disabled={busy}
              onChange={(e) => filters(e.target.value, state)}
            >
              <option value="all">All operations</option>
              <option value="indexing">Source indexing</option>
              <option value="generation">Draft generation</option>
              <option value="handling">Replies and ticket changes</option>
            </select>
          </label>
          <label>
            State
            <select
              value={state}
              disabled={busy}
              onChange={(e) => filters(kind, e.target.value)}
            >
              <option value="all">All states</option>
              {[
                "queued",
                "processing",
                "succeeded",
                "failed",
                "cancelled",
                "escalated",
                "confirmed",
                "archived",
                "deleted",
              ].map((s) => (
                <option key={s} value={s}>
                  {label(s)}
                </option>
              ))}
            </select>
          </label>
          <button
            className="secondary"
            disabled={busy || !workspaceId}
            onClick={reload}
          >
            Refresh activity
          </button>
        </div>
        {error && (
          <div className="alert error" role="alert">
            {error}
            <p>
              Saved work is retained. Refresh to check whether recovery was
              already queued before trying again.
            </p>
            <Link href="/">Demo entry</Link>
          </div>
        )}
        {notice && (
          <p role="status" className="save-notice">
            {notice}
          </p>
        )}
        {feed?.source_operations_admin_only && (
          <p className="small muted">
            Source indexing and unpublished-source history are visible only to
            Workspace Admins.
          </p>
        )}
        <div className="activity-layout">
          <section aria-labelledby="operations-title">
            <h2 id="operations-title">
              Operations{" "}
              {feed && <span className="small muted">({feed.total})</span>}
            </h2>
            {loading ? (
              <p role="status">Loading activity…</p>
            ) : !feed?.items.length ? (
              <p>No operations match these filters.</p>
            ) : (
              <ul className="activity-list">
                {feed.items.map((row) => (
                  <li key={`${row.kind}/${row.id}`}>
                    <button
                      className="activity-row"
                      aria-pressed={selected?.id === row.id}
                      onClick={() => {
                        setSelected({ id: row.id, kind: row.kind });
                        setDetail(null);
                        setError("");
                      }}
                    >
                      <span className="small muted">
                        {kindName(row)} ·{" "}
                        {row.mode === "deepseek"
                          ? "DeepSeek"
                          : row.kind === "generation"
                            ? "Fixture"
                            : ""}
                      </span>
                      <strong>{row.title}</strong>
                      <span className="badge">{label(row.status)}</span>
                      <time className="small muted" dateTime={row.updated_at}>
                        {new Date(row.updated_at).toLocaleString()}
                      </time>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {feed && feed.total > feed.limit && (
              <div className="form-actions">
                <button
                  className="secondary"
                  disabled={!offset || busy}
                  onClick={() => {
                    setOffset((v) => Math.max(0, v - feed.limit));
                    setLoading(true);
                  }}
                >
                  Previous
                </button>
                <span>
                  {offset + 1}–{Math.min(offset + feed.limit, feed.total)} of{" "}
                  {feed.total}
                </span>
                <button
                  className="secondary"
                  disabled={offset + feed.limit >= feed.total || busy}
                  onClick={() => {
                    setOffset((v) => v + feed.limit);
                    setLoading(true);
                  }}
                >
                  Next
                </button>
              </div>
            )}
          </section>
          <section
            className="activity-detail"
            aria-labelledby="operation-title"
          >
            <h2 ref={heading} id="operation-title" tabIndex={-1}>
              {detail ? kindName(detail) : "Operation details"}
            </h2>
            {!detail ? (
              <p className="muted">
                {selected
                  ? error
                    ? "Operation could not be loaded. Refresh activity to recover."
                    : "Loading operation…"
                  : "Choose an operation to inspect its history."}
              </p>
            ) : (
              <>
                <h3>{detail.title}</h3>
                <p>
                  <span className="badge">{label(detail.status)}</span>
                </p>
                <p>{detail.next_action}</p>
                {detail.kind === "indexing" && (
                  <p>
                    Attempts: {detail.attempts} of 3
                    {detail.lease_until && (
                      <>
                        {" "}
                        · Worker lock{" "}
                        {detail.lease_expired ? "expired" : "expires"}{" "}
                        <time dateTime={detail.lease_until}>
                          {new Date(detail.lease_until).toLocaleString()}
                        </time>
                      </>
                    )}
                  </p>
                )}
                <div className="form-actions">
                  {detail.can_retry && workspace?.role === "admin" && (
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => void retry()}
                    >
                      Retry indexing
                    </button>
                  )}
                  <Link
                    href={
                      detail.kind === "indexing"
                        ? `/knowledge?workspace=${workspaceId}&document=${detail.resource_id}`
                        : `/inbox?workspace=${workspaceId}&ticket=${detail.resource_id}`
                    }
                  >
                    {detail.kind === "indexing"
                      ? "Inspect source"
                      : "Open ticket"}
                  </Link>
                </div>
                <h3>Recorded history</h3>
                {!detail.timeline.length ? (
                  <p>
                    No transition history was recorded for this earlier
                    operation.
                  </p>
                ) : (
                  <ol className="operation-timeline">
                    {detail.timeline.map((event, i) => (
                      <li key={i}>
                        <strong>{label(event.phase)}</strong>
                        {event.attempt > 0 && (
                          <span> · attempt {event.attempt}</span>
                        )}
                        <p className="small muted">
                          {event.actor} ·{" "}
                          <time dateTime={event.created_at}>
                            {new Date(event.created_at).toLocaleString()}
                          </time>
                        </p>
                      </li>
                    ))}
                  </ol>
                )}
                <details>
                  <summary>Technical details</summary>
                  <dl>
                    <dt>Correlation ID</dt>
                    <dd>{detail.id}</dd>
                    <dt>Source or ticket ID</dt>
                    <dd>{detail.resource_id}</dd>
                  </dl>
                  <p className="small muted">{detail.history_note}</p>
                </details>
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
