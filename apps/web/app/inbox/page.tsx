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
import { TicketEvidence } from "@/components/ticket-evidence";
import { TicketHandling } from "@/components/ticket-handling";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  api,
  ApiError,
  type Workspace,
  type Member,
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
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [retry, setRetry] = useState(0);
  const [members, setMembers] = useState<Member[]>([]);
  const [hasUnsaved, setHasUnsaved] = useState(false);
  const [queueVersion, setQueueVersion] = useState(0);
  const [search, setSearch] = useState({
    q: "",
    status: "all",
    assignment: "all",
  });
  const selectedWorkspace = useRef("");
  const selectedTicket = useRef("");
  function canNavigate() {
    return (
      !hasUnsaved ||
      window.confirm("Discard your unsaved edits and leave this ticket?")
    );
  }
  function changed(next: TicketDetail) {
    if (
      selectedWorkspace.current !== workspaceId ||
      selectedTicket.current !== next.id
    )
      return;
    setDetail(next);
    setTickets((rows) => rows.map((t) => (t.id === next.id ? next : t)));
    setQueueVersion((v) => v + 1);
  }
  const hadDetailOpen = useRef(false);
  const workspace = workspaces.find((w) => w.id === workspaceId);
  function fail(error: unknown) {
    if (error instanceof Error && error.name === "AbortError") return;
    if (
      error instanceof ApiError &&
      [401, 403, 404, 410].includes(error.status)
    ) {
      setTickets([]);
      selectedTicket.current = "";
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
        const params = new URLSearchParams(window.location.search);
        setSearch({
          q: params.get("q") ?? "",
          status: params.get("status") ?? "all",
          assignment: params.get("assignment") ?? "all",
        });
        const nextId = rows.some((w) => w.id === selectedWorkspace.current)
          ? selectedWorkspace.current
          : (rows[0]?.id ?? "");
        if (nextId !== selectedWorkspace.current) {
          setTickets([]);
          selectedTicket.current = "";
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
    const params = new URLSearchParams(window.location.search);
    Promise.all([
      api<Ticket[]>(
        `workspaces/${workspaceId}/tickets?${params}`,
        "GET",
        controller.signal,
      ),
      api<Member[]>(
        `workspaces/${workspaceId}/members`,
        "GET",
        controller.signal,
      ),
    ])
      .then(([rows, people]) => {
        if (selectedWorkspace.current !== workspaceId) return;
        setMembers(people);
        setTickets(rows);
        if (!selectedTicket.current) selectedTicket.current = rows[0]?.id ?? "";
        setTicketId(selectedTicket.current);
        setLoading(false);
      })
      .catch(fail);
    return () => controller.abort();
  }, [workspaceId, retry, queueVersion]);
  useEffect(() => {
    if (!ticketId || !workspaceId) return;
    const controller = new AbortController();
    api<TicketDetail>(
      `workspaces/${workspaceId}/tickets/${ticketId}`,
      "GET",
      controller.signal,
    )
      .then((next) => {
        if (
          selectedWorkspace.current === workspaceId &&
          selectedTicket.current === ticketId
        )
          setDetail(next);
      })
      .catch(fail);
    return () => controller.abort();
  }, [ticketId, workspaceId, retry]);
  useEffect(() => {
    if (detailOpen && detail?.id) {
      document.querySelector<HTMLElement>(".ticket-detail h2")?.focus();
      hadDetailOpen.current = true;
    } else if (!detailOpen && hadDetailOpen.current) {
      document
        .querySelector<HTMLElement>(".ticket-row[aria-pressed=true]")
        ?.focus();
      hadDetailOpen.current = false;
    }
  }, [detailOpen, detail?.id]);
  async function leave() {
    if (!canNavigate()) return;
    const result = await authClient.signOut();
    if (result.error) {
      setError("Couldn't end this session. Try again.");
      return;
    }
    router.push("/");
  }
  function changeWorkspace(id: string) {
    if (!canNavigate()) return;
    setMembers([]);
    selectedWorkspace.current = id;
    setWorkspaceId(id);
    setTickets([]);
    selectedTicket.current = "";
    setTicketId("");
    setDetail(null);
    setError("");
    setLoading(true);
    setDetailOpen(false);
  }
  return (
    <div className="shell">
      <header className="app-header">
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
      <aside className="rail">
        <nav aria-label="Main navigation">
          <Link
            href="/inbox"
            onClick={(e) => {
              if (!canNavigate()) e.preventDefault();
            }}
            className="nav-item active"
            aria-current="page"
          >
            <Inbox size={18} />
            Inbox
          </Link>
          <Link
            href={`/knowledge?workspace=${workspaceId}`}
            onClick={(e) => {
              if (!canNavigate()) e.preventDefault();
            }}
            className="nav-item"
          >
            <BookOpen size={18} />
            Knowledge
          </Link>
          {[
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
          <span className="small muted">Manual handling</span>
        </div>
      </aside>
      <main id="main" className="workspace-main">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">
              {workspace ? `${workspace.name} · Fixture` : "Support workspace"}
            </span>
            <h1>All conversations</h1>
            <Link
              className="mobile-knowledge"
              href={`/knowledge?workspace=${workspaceId}`}
              onClick={(e) => {
                if (!canNavigate()) e.preventDefault();
              }}
            >
              Knowledge
            </Link>
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
              <form
                className="queue-filters"
                onSubmit={(e) => {
                  e.preventDefault();
                  const params = new URLSearchParams();
                  if (search.q) params.set("q", search.q);
                  if (search.status !== "all")
                    params.set("status", search.status);
                  if (search.assignment !== "all")
                    params.set("assignment", search.assignment);
                  window.history.replaceState(
                    null,
                    "",
                    `/inbox${params.size ? `?${params}` : ""}`,
                  );
                  setError("");
                  setLoading(true);
                  setQueueVersion((v) => v + 1);
                }}
              >
                <label>
                  Search conversations
                  <input
                    type="search"
                    maxLength={200}
                    value={search.q}
                    onChange={(e) =>
                      setSearch({ ...search, q: e.target.value })
                    }
                    placeholder="Subject, customer or email"
                  />
                </label>
                <label>
                  Status
                  <select
                    value={search.status}
                    onChange={(e) =>
                      setSearch({ ...search, status: e.target.value })
                    }
                  >
                    {["all", "open", "pending", "resolved"].map((v) => (
                      <option key={v} value={v}>
                        {v === "all" ? "All statuses" : v}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Assignment
                  <select
                    value={search.assignment}
                    onChange={(e) =>
                      setSearch({ ...search, assignment: e.target.value })
                    }
                  >
                    <option value="all">Anyone</option>
                    <option value="mine">Assigned to me</option>
                    <option value="unassigned">Unassigned</option>
                  </select>
                </label>
                <button className="secondary">Filter inbox</button>
              </form>
              <div className="queue-heading">
                <h2>All tickets</h2>
                <span className="badge">{tickets.length}</span>
              </div>
              {!loading && tickets.length > 0 && (
                <div className="queue-columns" aria-hidden="true">
                  <span>Customer</span>
                  <span>Conversation</span>
                  <span>Status</span>
                  <span>Priority</span>
                </div>
              )}
              {loading ? (
                <p className="loading" role="status">
                  Loading your inbox…
                </p>
              ) : error && !tickets.length ? (
                <p className="queue-note">
                  The ticket queue could not be loaded. Use Try again above to
                  reconnect.
                </p>
              ) : !tickets.length ? (
                <p className="queue-note">
                  {workspaces.length
                    ? "No tickets match these filters."
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
                      if (ticketId !== t.id && !canNavigate()) return;
                      if (ticketId !== t.id) setDetail(null);
                      selectedTicket.current = t.id;
                      setTicketId(t.id);
                      setEvidenceOpen(false);
                      setDetailOpen(true);
                    }}
                  >
                    <span className="row-customer">
                      {t.customer_name}
                      <span className="small muted">{t.customer_email}</span>
                    </span>
                    <span className="row-subject">
                      <strong>{t.subject}</strong>
                      <span className="small muted">Ticket #{t.number}</span>
                    </span>
                    <span className="badge open">{t.status}</span>
                    <span className="row-priority">{t.priority}</span>
                  </button>
                ))
              )}
            </section>
            <div
              className={`conversation-layout ${evidenceOpen ? "evidence-open" : "conversation-open"}`}
            >
              {detail && (
                <nav className="evidence-navigation" aria-label="Ticket panels">
                  <button
                    className="secondary"
                    onClick={() => setDetailOpen(false)}
                  >
                    Back to inbox
                  </button>
                  <button
                    className="secondary"
                    aria-pressed={!evidenceOpen}
                    onClick={() => setEvidenceOpen(false)}
                  >
                    Conversation
                  </button>
                  <button
                    className="secondary"
                    aria-pressed={evidenceOpen}
                    onClick={() => setEvidenceOpen(true)}
                  >
                    Evidence
                  </button>
                </nav>
              )}
              <section
                className="ticket-detail"
                aria-label="Ticket conversation"
              >
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
                    {!loading && !tickets.some((t) => t.id === detail.id) && (
                      <p className="small muted">
                        This selected ticket is outside the current filter
                        results.
                      </p>
                    )}
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
                    <TicketHandling
                      key={`${workspaceId}/${detail.id}`}
                      detail={detail}
                      workspaceId={workspaceId}
                      members={members}
                      readOnly={workspace?.role === "viewer"}
                      onChanged={changed}
                      onDirty={setHasUnsaved}
                    />
                  </>
                ) : (
                  <p className="loading" role="status">
                    {error
                      ? "The conversation could not be loaded. Use Try again above to reconnect."
                      : ticketId
                        ? "Loading the conversation…"
                        : "Choose a ticket to read its conversation."}
                  </p>
                )}
              </section>
              {detail && (
                <aside className="ticket-context" aria-label="Ticket details">
                  <TicketEvidence
                    key={`${workspaceId}/${detail.id}`}
                    workspaceId={workspaceId}
                    ticketId={detail.id}
                    revision={detail.revision}
                    readOnly={workspace?.role === "viewer"}
                  />
                  <span className="eyebrow">Conversation context</span>
                  <h3>Ticket details</h3>
                  <dl>
                    <dt>Customer</dt>
                    <dd>{detail.customer_name}</dd>
                    <dt>Email</dt>
                    <dd>{detail.customer_email}</dd>
                    <dt>Created</dt>
                    <dd>
                      <time dateTime={detail.created_at}>
                        {new Date(detail.created_at).toLocaleDateString(
                          undefined,
                          { month: "short", day: "numeric", year: "numeric" },
                        )}
                      </time>
                    </dd>
                    <dt>Your access</dt>
                    <dd>{workspace?.role}</dd>
                  </dl>
                  <p className="context-note">
                    <ShieldCheck size={18} aria-hidden="true" /> Synthetic
                    conversation, saved in your isolated workspace. No email
                    delivery is connected.
                  </p>
                </aside>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
