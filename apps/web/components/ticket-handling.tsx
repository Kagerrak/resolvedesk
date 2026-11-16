"use client";
import { useEffect, useState } from "react";
import { api, ApiError, type Member, type TicketDetail } from "@/lib/api";

type Props = {
  detail: TicketDetail;
  workspaceId: string;
  readOnly: boolean;
  members: Member[];
  onChanged: (ticket: TicketDetail) => void;
  onDirty: (dirty: boolean) => void;
};

export function TicketHandling({
  detail,
  workspaceId,
  readOnly,
  members,
  onChanged,
  onDirty,
}: Props) {
  const [body, setBody] = useState(detail.draft?.body ?? "");
  const [status, setStatus] = useState(detail.status);
  const [priority, setPriority] = useState(detail.priority);
  const [assignee, setAssignee] = useState(detail.assigned_to ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [accessEnded, setAccessEnded] = useState(false);
  const [notice, setNotice] = useState("");
  const draftDirty = body !== (detail.draft?.body ?? "");
  const fieldsDirty =
    status !== detail.status ||
    priority !== detail.priority ||
    assignee !== (detail.assigned_to ?? "");
  const dirty = !readOnly && (draftDirty || fieldsDirty);
  const path = `workspaces/${workspaceId}/tickets/${detail.id}`;
  useEffect(() => {
    onDirty(dirty);
    return () => onDirty(false);
  }, [dirty, onDirty]);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  async function save(kind: "draft" | "fields" | "reopen") {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const next = await api<TicketDetail>(
        kind === "draft" ? `${path}/draft` : path,
        kind === "draft" ? "POST" : "PATCH",
        undefined,
        kind === "draft"
          ? { expected_revision: detail.revision, body }
          : {
              expected_revision: detail.revision,
              status: kind === "reopen" ? "open" : status,
              priority,
              assigned_to: assignee || null,
              reopen: kind === "reopen",
            },
      );
      onChanged(next);
      if (kind !== "draft") {
        setStatus(next.status);
        setPriority(next.priority);
        setAssignee(next.assigned_to ?? "");
      }
      setNotice(
        kind === "draft"
          ? "Draft saved. No email was sent."
          : kind === "reopen"
            ? "Ticket reopened."
            : "Ticket changes saved.",
      );
    } catch (reason) {
      setConflict(reason instanceof ApiError && reason.status === 409);
      setAccessEnded(
        reason instanceof ApiError && [401, 404, 410].includes(reason.status),
      );
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not save. Your edits are still here.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function loadLatest() {
    setBusy(true);
    setError("");
    try {
      const latest = await api<TicketDetail>(path);
      onChanged(latest);
      setConflict(false);
      setNotice(
        "Latest version loaded. Your local edits are retained. Compare the saved values below before saving again.",
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not load the latest version.",
      );
    } finally {
      setBusy(false);
    }
  }
  const memberName = (id: string | null) =>
    id
      ? (members.find((m) => m.user_id === id)?.name ??
        "Former workspace member")
      : "Unassigned";
  return (
    <div className="handling">
      {readOnly && (
        <div className="alert">
          <h3>You have read-only access</h3>
          <p>
            An Agent or Admin handles changes and replies. You can inspect the
            saved draft and history.
          </p>
        </div>
      )}
      <section aria-labelledby="handling-title">
        <h3 id="handling-title">Ticket handling</h3>
        <p className="small muted">
          Saved: {detail.status} · {detail.priority} priority ·{" "}
          {memberName(detail.assigned_to)}
        </p>
        {!readOnly && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void save("fields");
            }}
          >
            <fieldset disabled={busy || conflict} className="handling-fields">
              <legend className="sr-only">Choose ticket changes</legend>
              <label>
                Status
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  disabled={detail.status === "resolved"}
                >
                  {detail.status === "resolved" ? (
                    <option value="resolved">Resolved</option>
                  ) : (
                    <>
                      <option value="open">Open</option>
                      <option value="pending">Pending</option>
                      <option value="resolved">Resolved</option>
                    </>
                  )}
                </select>
              </label>
              <label>
                Priority
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  {["low", "normal", "high", "urgent"].map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Assigned to
                <select
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                >
                  <option value="">Unassigned</option>
                  {members
                    .filter((m) => m.role !== "viewer")
                    .map((m) => (
                      <option key={m.user_id} value={m.user_id}>
                        {m.name}
                      </option>
                    ))}
                </select>
              </label>
            </fieldset>
            <div className="form-actions">
              <button
                className="secondary"
                disabled={busy || conflict || !fieldsDirty}
              >
                Apply ticket changes
              </button>
              {detail.status === "resolved" && (
                <button
                  type="button"
                  className="secondary"
                  disabled={busy || conflict}
                  onClick={() => void save("reopen")}
                >
                  Reopen ticket
                </button>
              )}
            </div>
          </form>
        )}
      </section>
      <section aria-labelledby="draft-title" className="draft-panel">
        <header>
          <h3 id="draft-title">Manual draft</h3>
          <span className="badge">Not sent</span>
        </header>
        {readOnly ? (
          <p className="message-body">
            {detail.draft?.body || "No saved draft yet."}
          </p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void save("draft");
            }}
          >
            <label htmlFor="draft-body" className="sr-only">
              Draft reply
            </label>
            <textarea
              id="draft-body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              maxLength={20000}
              rows={7}
              disabled={busy}
              aria-describedby="draft-help"
              placeholder="Write a reply for review…"
            />
            <p id="draft-help" className="small muted">
              Saving keeps a draft revision. Sending and approval are not
              available yet.
            </p>
            <div className="form-actions">
              <button
                className="primary"
                disabled={busy || conflict || !draftDirty}
              >
                Save draft
              </button>
              <span className="small muted">
                {draftDirty
                  ? "Unsaved draft"
                  : detail.draft
                    ? "All draft edits saved"
                    : "No saved draft"}
              </span>
            </div>
            {notice.startsWith("Latest") && (
              <details>
                <summary>Compare latest saved draft</summary>
                <p className="message-body">
                  {detail.draft?.body || "No saved draft."}
                </p>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    setBody(detail.draft?.body ?? "");
                    setStatus(detail.status);
                    setPriority(detail.priority);
                    setAssignee(detail.assigned_to ?? "");
                    setNotice("Latest saved values restored.");
                  }}
                >
                  Use latest saved values
                </button>
              </details>
            )}
          </form>
        )}
      </section>
      {error && (
        <div className="alert error" role="alert">
          {error}
          <p className="small">
            Your local edits are still here. A failed response may have saved;
            load the latest version before retrying.
          </p>
          {accessEnded ? (
            <a href="/">Return to demo entry</a>
          ) : (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void loadLatest()}
            >
              Load latest version
            </button>
          )}
        </div>
      )}
      {notice && (
        <p role="status" className="save-notice">
          {notice}
        </p>
      )}
      <section aria-labelledby="history-title" className="ticket-history">
        <h3 id="history-title">Handling history</h3>
        {!detail.events.length ? (
          <p className="muted">No handling changes yet.</p>
        ) : (
          <ol>
            {detail.events.map((event) => (
              <li key={event.id}>
                <strong>
                  {event.action === "draft_saved"
                    ? "Draft saved · not sent"
                    : event.action === "ticket_reopened"
                      ? "Ticket reopened"
                      : "Ticket updated"}
                </strong>
                <span className="small muted">
                  {event.actor} ·{" "}
                  <time dateTime={event.created_at}>
                    {new Date(event.created_at).toLocaleString()}
                  </time>
                </span>
                {event.action !== "draft_saved" && (
                  <ul>
                    {Object.entries(event.changes).map(([field, change]) =>
                      typeof change === "string" ? null : (
                        <li key={field}>
                          {field === "assigned_to" ? "Assignment" : field}:{" "}
                          {field === "assigned_to"
                            ? memberName(change.before)
                            : change.before}{" "}
                          →{" "}
                          {field === "assigned_to"
                            ? memberName(change.after)
                            : change.after}
                        </li>
                      ),
                    )}
                  </ul>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
