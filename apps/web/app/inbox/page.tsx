"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  Inbox,
  Activity,
  ChartNoAxesColumn,
  Settings,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  api,
  ApiError,
  type Workspace,
  type Ticket,
  type TicketDetail,
} from "@/lib/api";
import { authClient } from "@/lib/auth-client";

export default function InboxPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketId, setTicketId] = useState("");
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailOpen, setDetailOpen] = useState(false);
  const [retry, setRetry] = useState(0);
  const selectedWorkspace = useRef("");
  const hadDetailOpen = useRef(false);
  const workspace = workspaces.find((w) => w.id === workspaceId);
  function fail(error: unknown) {
    if (error instanceof Error && error.name === "AbortError") return;
    if (
      error instanceof ApiError &&
      [401, 403, 404, 410].includes(error.status)
    ) {
      setTickets([]);
      setTicketId("");
      setDetail(null);
    }
    if (error instanceof ApiError && error.status === 401) {
      setExpired(true);
      setWorkspaces([]);
      setTickets([]);
      setDetail(null);
    }
    setError(
      error instanceof Error ? error.message : "Could not load your workspace.",
    );
    setLoading(false);
  }
  useEffect(() => {
    const controller = new AbortController();
    api<Workspace[]>("workspaces", "GET", controller.signal)
      .then((rows) => {
        setWorkspaces(rows);
        const nextId = rows.some((w) => w.id === selectedWorkspace.current)
          ? selectedWorkspace.current
          : (rows[0]?.id ?? "");
        if (nextId !== selectedWorkspace.current) {
          setTickets([]);
          setTicketId("");
          setDetail(null);
          setDetailOpen(false);
        }
        selectedWorkspace.current = nextId;
        setWorkspaceId(nextId);
        if (!rows.length) setLoading(false);
      })
      .catch(fail);
    return () => controller.abort();
  }, [retry]);
  useEffect(() => {
    if (!workspaceId) return;
    const controller = new AbortController();
    api<Ticket[]>(`workspaces/${workspaceId}/tickets`, "GET", controller.signal)
      .then((rows) => {
        setTickets(rows);
        setTicketId(rows[0]?.id ?? "");
        setLoading(false);
      })
      .catch(fail);
    return () => controller.abort();
  }, [workspaceId, retry]);
  useEffect(() => {
    if (!ticketId || !workspaceId) return;
    const controller = new AbortController();
    api<TicketDetail>(
      `workspaces/${workspaceId}/tickets/${ticketId}`,
      "GET",
      controller.signal,
    )
      .then(setDetail)
      .catch(fail);
    return () => controller.abort();
  }, [ticketId, workspaceId, retry]);
  useEffect(() => {
    if (detailOpen && detail) {
      document.querySelector<HTMLElement>(".ticket-detail h2")?.focus();
      hadDetailOpen.current = true;
    } else if (!detailOpen && hadDetailOpen.current) {
      document
        .querySelector<HTMLElement>(".ticket-row[aria-pressed=true]")
        ?.focus();
      hadDetailOpen.current = false;
    }
  }, [detailOpen, detail]);
  async function leave() {
    const result = await authClient.signOut();
    if (result.error) {
      setError("Couldn't end this session. Try again.");
      return;
    }
    router.push("/");
  }
  function changeWorkspace(id: string) {
    selectedWorkspace.current = id;
    setWorkspaceId(id);
    setTickets([]);
    setTicketId("");
    setDetail(null);
    setError("");
    setLoading(true);
    setDetailOpen(false);
  }
  return (
    <div className="shell">
      <aside className="rail">
        <Brand />
        <div className="workspace-picker">
          <label className="workspace-label" htmlFor="workspace">
            Workspace
          </label>
          <select
            id="workspace"
            aria-label="Workspace"
            className="workspace-select"
            value={workspaceId}
            onChange={(e) => changeWorkspace(e.target.value)}
            disabled={!workspaces.length}
          >
            {!workspaces.length && <option value="">No workspace</option>}
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>
        <nav aria-label="Main navigation">
          <Link href="/inbox" className="nav-item active" aria-current="page">
            <Inbox size={18} />
            Inbox
          </Link>
          {[
            { icon: BookOpen, label: "Knowledge" },
            { icon: Activity, label: "Activity" },
            { icon: ChartNoAxesColumn, label: "Quality" },
            { icon: Settings, label: "Settings" },
          ].map(({ icon: Glyph, label }) => {
            return (
              <span className="nav-item" key={String(label)}>
                <Glyph size={18} />
                {String(label)}
                <span className="soon">Planned</span>
              </span>
            );
          })}
        </nav>
        <div className="rail-footer">
          <span className="small muted">
            <ShieldCheck size={14} /> Isolated synthetic workspace
          </span>
          <span className="small muted">Early preview · S01</span>
        </div>
      </aside>
      <main id="main" className="workspace-main">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">Meridian support</span>
            <h1>Inbox</h1>
          </div>
          <div className="header-actions">
            <span className="badge">Fixture mode</span>
            <ThemeToggle />
            <button
              className="icon-button"
              onClick={leave}
              aria-label="End demo session"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        {error && (
          <div className="alert error" role="alert">
            {error}{" "}
            {expired ? (
              <Link href="/">Start a new demo</Link>
            ) : (
              <button
                className="secondary"
                onClick={() => {
                  setError("");
                  setLoading(true);
                  setRetry((v) => v + 1);
                }}
              >
                Try again
              </button>
            )}
          </div>
        )}
        {!expired && (
          <div className={`inbox ${detailOpen ? "detail-open" : ""}`}>
            <section className="queue" aria-label="Ticket queue">
              <div className="queue-heading">
                <h2>All tickets</h2>
                <span className="badge">{tickets.length}</span>
              </div>
              {loading ? (
                <p className="loading" role="status">
                  Loading your inbox…
                </p>
              ) : !tickets.length ? (
                <p className="queue-note">
                  {workspaces.length
                    ? "Your queue is clear."
                    : "No active workspace is available."}{" "}
                  {!workspaces.length && (
                    <Link href="/">Return to demo entry</Link>
                  )}
                </p>
              ) : (
                tickets.map((t) => (
                  <button
                    key={t.id}
                    className="ticket-row"
                    aria-pressed={ticketId === t.id}
                    onClick={() => {
                      if (ticketId !== t.id) setDetail(null);
                      setTicketId(t.id);
                      setDetailOpen(true);
                    }}
                  >
                    <span className="row-top">
                      <span>{t.customer_name}</span>
                      <span>#{t.number}</span>
                    </span>
                    <strong>{t.subject}</strong>
                    <p>Role changes and project permissions</p>
                    <span className="badge open">{t.status}</span>
                  </button>
                ))
              )}
              <p className="queue-note">
                A sample conversation.
                <br />A workspace that belongs only to you.
              </p>
            </section>
            <section className="ticket-detail" aria-label="Ticket conversation">
              <button
                className="secondary mobile-back"
                onClick={() => setDetailOpen(false)}
              >
                <ArrowLeft size={16} />
                Back to inbox
              </button>
              {detail ? (
                <>
                  <span className="eyebrow">
                    Ticket #{detail.number} · Email
                  </span>
                  <h2 tabIndex={-1}>{detail.subject}</h2>
                  <div className="ticket-meta">
                    <span className="badge open">{detail.status}</span>
                    <span>{detail.priority} priority</span>
                    <span>{workspace?.role} access</span>
                    <span>Fixture · no email delivery</span>
                  </div>
                  {detail.messages.map((m) => (
                    <article key={m.id} className="message">
                      <header className="message-header">
                        <span className="avatar" aria-hidden="true">
                          {m.sender_name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                        <div>
                          <strong>{m.sender_name}</strong>
                          <div className="small muted">{m.sender_email}</div>
                        </div>
                        <time dateTime={m.created_at}>
                          {new Date(m.created_at).toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                        </time>
                      </header>
                      <p className="message-body">{m.body}</p>
                    </article>
                  ))}
                  <aside className="next-step">
                    <h3>
                      {workspace?.role === "viewer"
                        ? "You have read-only access"
                        : "The conversation comes first"}
                    </h3>
                    <p className="muted">
                      {workspace?.role === "viewer"
                        ? "You can inspect this conversation. An Agent or Admin handles changes and replies."
                        : "This preview lets you inspect a saved ticket. Manual handling and cited reply assistance arrive in the next slices."}
                    </p>
                    <span className="small muted">
                      No reply has been drafted, approved or sent.
                    </span>
                  </aside>
                </>
              ) : (
                <p className="loading" role="status">
                  {ticketId
                    ? "Loading the conversation…"
                    : "Choose a ticket to read its conversation."}
                </p>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
